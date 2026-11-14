"""Generate release metadata for the documentation site.

Reads the declared version from ``origin/main``, ``origin/dev``, and
``origin/test_pypi`` with ``git show``. Fetches the latest releases from
PyPI and TestPyPI with a timeout. Writes a JSON artifact for continuous
integration and a Markdown partial for the releases page.

A missing branch or an unreachable index does not fail the command. The
output records the failure and the page labels the data as unavailable.

Usage:
    python scripts/generate_release_metadata.py
    python scripts/generate_release_metadata.py --json JSON --markdown MD
"""

from __future__ import annotations

import argparse
import http.client
import json
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from packaging.version import InvalidVersion, Version

BRANCHES = ("main", "dev", "test_pypi")
INDEXES = {
    "pypi": "https://pypi.org/pypi/ramtable/json",
    "test_pypi": "https://test.pypi.org/pypi/ramtable/json",
}
PROJECT_URLS = {
    "pypi": "https://pypi.org/project/ramtable",
    "test_pypi": "https://test.pypi.org/project/ramtable",
}
DEFAULT_JSON = Path("docs/_data/release-metadata.json")
DEFAULT_MARKDOWN = Path("docs/_generated/release-metadata.md")
TIMEOUT_SECONDS = 10
RETRIES = 2
USER_AGENT = "ramtable-docs/1"
RELATIONS = {"ahead", "behind", "equal", "invalid", "unavailable"}


def _git_show(ref: str) -> str:
    """Return the ``pyproject.toml`` stored at ``ref``."""

    completed = subprocess.run(
        ["git", "show", f"{ref}:pyproject.toml"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or f"git show failed for {ref}"
        raise RuntimeError(message)
    return completed.stdout


def read_branch_versions(
    git_show: Callable[[str], str] = _git_show,
) -> dict[str, dict[str, Any]]:
    """Read the declared version of each release branch from Git."""

    branches: dict[str, dict[str, Any]] = {}
    for branch in BRANCHES:
        ref = f"origin/{branch}"
        try:
            config = tomllib.loads(git_show(ref))
            version = str(config["project"]["version"])
            Version(version)
        except InvalidVersion:
            branches[branch] = {
                "ref": ref,
                "version": None,
                "available": False,
                "error": f"InvalidVersion: {version}",
            }
        except Exception as error:  # noqa: BLE001
            branches[branch] = {
                "ref": ref,
                "version": None,
                "available": False,
                "error": f"{type(error).__name__}: {error}",
            }
        else:
            branches[branch] = {
                "ref": ref,
                "version": version,
                "available": True,
                "error": None,
            }
    return branches


def _http_get(url: str, timeout: int) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _parse_index_payload(
    name: str, url: str, payload: bytes
) -> dict[str, Any]:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("index payload must be an object")
    info = data.get("info")
    if not isinstance(info, dict):
        raise ValueError("index payload is missing info")
    latest = info.get("version")
    if not isinstance(latest, str):
        raise ValueError("index payload is missing info.version")
    try:
        Version(latest)
    except InvalidVersion as error:
        raise ValueError(f"invalid latest version: {latest!r}") from error

    releases_data = data.get("releases", {})
    if not isinstance(releases_data, dict):
        raise ValueError("index payload releases must be an object")

    releases = []
    for version, files in releases_data.items():
        if not isinstance(version, str) or not isinstance(files, list):
            continue
        try:
            Version(version)
        except InvalidVersion:
            continue
        uploaded = [
            item["upload_time_iso_8601"]
            for item in files
            if isinstance(item, dict)
            and isinstance(item.get("upload_time_iso_8601"), str)
        ]
        if not uploaded:
            continue
        releases.append(
            {
                "version": version,
                "uploaded": min(uploaded),
                "url": f"{PROJECT_URLS[name]}/{quote(version, safe='')}/",
            }
        )
    releases.sort(key=lambda item: item["uploaded"], reverse=True)
    return {
        "url": url,
        "available": True,
        "latest": latest,
        "releases": releases[:5],
        "error": None,
    }


def fetch_index(
    name: str,
    url: str | None = None,
    *,
    fetch: Callable[[str, int], bytes] = _http_get,
    sleep: Callable[[float], None] = time.sleep,
    timeout: int = TIMEOUT_SECONDS,
    retries: int = RETRIES,
) -> dict[str, Any]:
    """Return the latest releases from one package index."""

    index_url = url or INDEXES[name]
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            payload = fetch(index_url, timeout)
            return _parse_index_payload(name, index_url, payload)
        except (
            OSError,
            URLError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            http.client.HTTPException,
        ) as error:
            last_error = error
            if attempt < retries:
                sleep(float(attempt + 1))
    return {
        "url": index_url,
        "available": False,
        "latest": None,
        "releases": [],
        "error": (
            f"{type(last_error).__name__}: {last_error}"
            if last_error is not None
            else "unavailable"
        ),
    }


def compare_versions(left: str | None, right: str | None) -> str:
    """Compare two versions with PEP 440 ordering."""

    if not left or not right:
        return "unavailable"
    try:
        left_version = Version(left)
        right_version = Version(right)
    except InvalidVersion:
        return "invalid"
    if left_version > right_version:
        return "ahead"
    if left_version < right_version:
        return "behind"
    return "equal"


def build_metadata(
    branches: dict[str, dict[str, Any]],
    indexes: dict[str, dict[str, Any]],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Combine branch and index data into one metadata document."""

    def branch_version(name: str) -> str | None:
        return (branches.get(name) or {}).get("version")

    def index_latest(name: str) -> str | None:
        return (indexes.get(name) or {}).get("latest")

    relations = {
        "main_vs_pypi": compare_versions(
            branch_version("main"), index_latest("pypi")
        ),
        "test_pypi_vs_test_pypi": compare_versions(
            branch_version("test_pypi"), index_latest("test_pypi")
        ),
        "dev_vs_main": compare_versions(
            branch_version("dev"), branch_version("main")
        ),
    }
    return {
        "generated_at": generated_at,
        "branches": branches,
        "indexes": indexes,
        "relations": relations,
    }


def validate_metadata(metadata: dict[str, Any]) -> None:
    """Raise ``ValueError`` when the metadata shape is invalid."""

    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary")
    for key in ("generated_at", "branches", "indexes", "relations"):
        if key not in metadata:
            raise ValueError(f"metadata is missing {key!r}")
    if not isinstance(metadata["branches"], dict):
        raise ValueError("metadata branches must be a dictionary")
    if not isinstance(metadata["indexes"], dict):
        raise ValueError("metadata indexes must be a dictionary")
    if not isinstance(metadata["relations"], dict):
        raise ValueError("metadata relations must be a dictionary")
    for name in BRANCHES:
        branch = metadata["branches"].get(name)
        if branch is None:
            continue
        if not isinstance(branch, dict):
            raise ValueError(f"branch {name!r} must be a dictionary")
        if not isinstance(branch.get("available"), bool):
            raise ValueError(f"branch {name!r} needs an available flag")
        if branch.get("version") is not None and not isinstance(
            branch["version"], str
        ):
            raise ValueError(f"branch {name!r} has an invalid version")
        if branch.get("error") is not None and not isinstance(
            branch["error"], str
        ):
            raise ValueError(f"branch {name!r} has an invalid error")
    for name in ("pypi", "test_pypi"):
        index = metadata["indexes"].get(name)
        if index is None:
            raise ValueError(f"metadata is missing index {name!r}")
        if not isinstance(index, dict):
            raise ValueError(f"index {name!r} must be a dictionary")
        if not isinstance(index.get("available"), bool):
            raise ValueError(f"index {name!r} needs an available flag")
        if not isinstance(index.get("releases"), list):
            raise ValueError(f"index {name!r} needs a releases list")
    for key, relation in metadata["relations"].items():
        if relation not in RELATIONS:
            raise ValueError(f"relation {key!r} has an invalid value")


def _escape_cell(value: object) -> str:
    text = " ".join(str(value).splitlines())
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "\\|")
        .replace("`", "\\`")
    )


def _render_branch_row(
    name: str, branch: dict[str, Any]
) -> str:
    if branch.get("available") and branch.get("version"):
        version = _escape_cell(branch["version"])
        return f"| `{name}` | `{version}` | available |"
    error = _escape_cell(branch.get("error") or "not available")
    return f"| `{name}` | unavailable | {error} |"


def _render_index(name: str, index: dict[str, Any]) -> list[str]:
    display_names = {"pypi": "PyPI", "test_pypi": "TestPyPI"}
    lines = [f"### {display_names[name]}", ""]
    if not index.get("available"):
        error = index.get("error") or "not available"
        lines.append(f"Data unavailable: {error}. The next build retries.")
        lines.append("")
        return lines
    lines.append(f"Latest release: `{_escape_cell(index['latest'])}`")
    lines.append("")
    releases = index.get("releases", [])
    if not releases:
        lines.append("No releases found.")
        lines.append("")
        return lines
    lines.extend(
        [
            "| Version | Uploaded | Link |",
            "|---|---|---|",
        ]
    )
    for release in releases:
        version = _escape_cell(release["version"])
        uploaded = _escape_cell(str(release["uploaded"])[:10])
        lines.append(
            f"| `{version}` | {uploaded} | "
            f"[project]({release['url']}) |"
        )
    lines.append("")
    return lines


def render_markdown(metadata: dict[str, Any]) -> str:
    """Render the metadata as a Markdown fragment."""

    lines = [
        "<!-- Generated by scripts/generate_release_metadata.py. -->",
        "",
        f"_Last attempt: {metadata['generated_at']}._",
        "",
        "### Branch versions",
        "",
        "| Branch | Declared version | Status |",
        "|---|---|---|",
    ]
    for name in BRANCHES:
        branch = metadata["branches"].get(name)
        if branch is None:
            lines.append(f"| `{name}` | unavailable | missing |")
        else:
            lines.append(_render_branch_row(name, branch))
    lines.append("")
    lines.extend(_render_index("pypi", metadata["indexes"]["pypi"]))
    lines.extend(
        _render_index("test_pypi", metadata["indexes"]["test_pypi"])
    )
    lines.extend(
        [
            "### Version relations",
            "",
            "| Comparison | Result |",
            "|---|---|",
            "| `main` against latest PyPI | "
            f"{metadata['relations']['main_vs_pypi']} |",
            "| `test_pypi` against latest TestPyPI | "
            f"{metadata['relations']['test_pypi_vs_test_pypi']} |",
            "| `dev` against `main` | "
            f"{metadata['relations']['dev_vs_main']} |",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    metadata: dict[str, Any],
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Validate the metadata and write both output files."""

    validate_metadata(metadata)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(metadata), encoding="utf-8")


def _now() -> str:
    current = datetime.now(timezone.utc).replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    """Generate the metadata files and return a process exit code."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON,
        help="JSON artifact path.",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=DEFAULT_MARKDOWN,
        help="Markdown fragment path.",
    )
    args = parser.parse_args(argv)

    branches = read_branch_versions()
    indexes = {
        name: fetch_index(name, url) for name, url in INDEXES.items()
    }
    metadata = build_metadata(
        branches, indexes, generated_at=_now()
    )
    try:
        write_outputs(metadata, args.json, args.markdown)
    except (OSError, ValueError) as error:
        print(f"release metadata: {error}", file=sys.stderr)
        return 1

    for name, index in indexes.items():
        if not index["available"]:
            print(
                f"release metadata: {name} unavailable: {index['error']}",
                file=sys.stderr,
            )
    print(f"Wrote {args.json} and {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
