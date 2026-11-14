"""Tests for the release metadata generator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_release_metadata.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_release_metadata", SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


grm = load_generator()


def test_read_branch_versions_reads_each_branch() -> None:
    def git_show(ref: str) -> str:
        versions = {
            "origin/main": "0.4.1",
            "origin/dev": "0.5.0.dev0",
            "origin/test_pypi": "0.5.0rc1",
        }
        return f'[project]\nversion = "{versions[ref]}"\n'

    result = grm.read_branch_versions(git_show=git_show)

    assert result["main"]["version"] == "0.4.1"
    assert result["main"]["available"] is True
    assert result["dev"]["version"] == "0.5.0.dev0"
    assert result["test_pypi"]["version"] == "0.5.0rc1"


def test_read_branch_versions_records_a_missing_branch() -> None:
    def git_show(ref: str) -> str:
        if ref == "origin/test_pypi":
            raise RuntimeError("missing branch")
        return '[project]\nversion = "0.4.1"\n'

    result = grm.read_branch_versions(git_show=git_show)

    assert result["main"]["available"] is True
    assert result["test_pypi"]["available"] is False
    assert result["test_pypi"]["version"] is None
    assert "missing branch" in result["test_pypi"]["error"]


def test_fetch_index_sorts_releases_and_limits_history() -> None:
    payload = {
        "info": {"version": "0.4.1"},
        "releases": {
            "0.1.0": [
                {"upload_time_iso_8601": "2026-01-01T00:00:00.000000Z"}
            ],
            "0.2.0": [
                {"upload_time_iso_8601": "2026-02-01T00:00:00.000000Z"}
            ],
            "0.3.0": [
                {"upload_time_iso_8601": "2026-03-01T00:00:00.000000Z"}
            ],
            "0.4.0": [
                {"upload_time_iso_8601": "2026-04-01T00:00:00.000000Z"}
            ],
            "0.4.1": [
                {"upload_time_iso_8601": "2026-05-01T00:00:00.000000Z"}
            ],
            "0.5.0": [
                {"upload_time_iso_8601": "2026-06-01T00:00:00.000000Z"}
            ],
            "0.6.0": [],
        },
    }

    def fetch(url: str, timeout: int) -> bytes:
        return json.dumps(payload).encode("utf-8")

    result = grm.fetch_index("pypi", fetch=fetch, sleep=lambda _: None)

    assert result["available"] is True
    assert result["latest"] == "0.4.1"
    assert [release["version"] for release in result["releases"]] == [
        "0.5.0",
        "0.4.1",
        "0.4.0",
        "0.3.0",
        "0.2.0",
    ]
    assert result["releases"][0]["url"] == (
        "https://pypi.org/project/ramtable/0.5.0/"
    )


def test_fetch_index_retries_then_reports_an_error() -> None:
    calls: list[str] = []

    def fetch(url: str, timeout: int) -> bytes:
        calls.append(url)
        raise OSError("index offline")

    result = grm.fetch_index("pypi", fetch=fetch, sleep=lambda _: None)

    assert len(calls) == 3
    assert result["available"] is False
    assert result["latest"] is None
    assert result["releases"] == []
    assert "index offline" in result["error"]


def test_build_metadata_compares_versions() -> None:
    branches = {
        "main": {"version": "0.4.1", "available": True, "error": None},
        "dev": {"version": "0.5.0.dev0", "available": True, "error": None},
        "test_pypi": {
            "version": "0.4.1",
            "available": True,
            "error": None,
        },
    }
    indexes = {
        "pypi": {
            "available": True,
            "latest": "0.4.1",
            "releases": [],
            "error": None,
            "url": "https://pypi.org/project/ramtable/",
        },
        "test_pypi": {
            "available": True,
            "latest": "0.4.1",
            "releases": [],
            "error": None,
            "url": "https://test.pypi.org/project/ramtable/",
        },
    }

    metadata = grm.build_metadata(
        branches, indexes, generated_at="2026-11-14T00:00:00Z"
    )

    assert metadata["relations"]["main_vs_pypi"] == "equal"
    assert metadata["relations"]["test_pypi_vs_test_pypi"] == "equal"
    assert metadata["relations"]["dev_vs_main"] == "ahead"


def test_build_metadata_marks_relations_unavailable() -> None:
    branches = {
        "main": {"version": None, "available": False, "error": "missing"},
        "dev": {"version": None, "available": False, "error": "missing"},
        "test_pypi": {"version": None, "available": False, "error": "missing"},
    }
    indexes = {
        "pypi": {
            "available": False,
            "latest": None,
            "releases": [],
            "error": "offline",
            "url": "https://pypi.org/project/ramtable/",
        },
        "test_pypi": {
            "available": False,
            "latest": None,
            "releases": [],
            "error": "offline",
            "url": "https://test.pypi.org/project/ramtable/",
        },
    }

    metadata = grm.build_metadata(
        branches, indexes, generated_at="2026-11-14T00:00:00Z"
    )

    assert set(metadata["relations"].values()) == {"unavailable"}


def test_validate_metadata_rejects_missing_sections() -> None:
    with pytest.raises(ValueError):
        grm.validate_metadata({})


def test_write_outputs_writes_json_and_markdown(tmp_path: Path) -> None:
    metadata = {
        "generated_at": "2026-11-14T00:00:00Z",
        "branches": {
            "main": {
                "ref": "origin/main",
                "version": "0.4.1",
                "available": True,
                "error": None,
            },
            "dev": {
                "ref": "origin/dev",
                "version": "0.5.0.dev0",
                "available": True,
                "error": None,
            },
            "test_pypi": {
                "ref": "origin/test_pypi",
                "version": None,
                "available": False,
                "error": "missing branch",
            },
        },
        "indexes": {
            "pypi": {
                "url": "https://pypi.org/project/ramtable/",
                "available": True,
                "latest": "0.4.1",
                "releases": [
                    {
                        "version": "0.4.1",
                        "uploaded": "2026-05-01T00:00:00.000000Z",
                        "url": (
                            "https://pypi.org/project/ramtable/0.4.1/"
                        ),
                    }
                ],
                "error": None,
            },
            "test_pypi": {
                "url": "https://test.pypi.org/project/ramtable/",
                "available": False,
                "latest": None,
                "releases": [],
                "error": "index offline",
            },
        },
        "relations": {
            "main_vs_pypi": "equal",
            "test_pypi_vs_test_pypi": "unavailable",
            "dev_vs_main": "ahead",
        },
    }
    json_path = tmp_path / "_data" / "release-metadata.json"
    markdown_path = tmp_path / "_generated" / "release-metadata.md"

    grm.write_outputs(metadata, json_path, markdown_path)

    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["branches"]["main"]["version"] == "0.4.1"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "### Branch versions" in markdown
    assert "`0.4.1`" in markdown
    assert "missing branch" in markdown
    assert "index offline" in markdown
    assert "`dev` against `main`" in markdown


def test_main_exits_zero_when_an_index_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    branches = {
        "main": {
            "ref": "origin/main",
            "version": "0.4.1",
            "available": True,
            "error": None,
        },
        "dev": {
            "ref": "origin/dev",
            "version": "0.5.0.dev0",
            "available": True,
            "error": None,
        },
        "test_pypi": {
            "ref": "origin/test_pypi",
            "version": None,
            "available": False,
            "error": "missing branch",
        },
    }

    def fake_fetch_index(name: str, url: str | None = None):
        return {
            "url": url or "",
            "available": False,
            "latest": None,
            "releases": [],
            "error": "index offline",
        }

    monkeypatch.setattr(
        grm, "read_branch_versions", lambda: branches
    )
    monkeypatch.setattr(grm, "fetch_index", fake_fetch_index)

    exit_code = grm.main(
        [
            "--json",
            str(tmp_path / "metadata.json"),
            "--markdown",
            str(tmp_path / "metadata.md"),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "metadata.json").is_file()
    assert (tmp_path / "metadata.md").is_file()


def test_main_exits_nonzero_when_output_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(grm, "read_branch_versions", lambda: {})
    monkeypatch.setattr(
        grm,
        "fetch_index",
        lambda name, url=None: {
            "url": url or "",
            "available": False,
            "latest": None,
            "releases": [],
            "error": "offline",
        },
    )

    def fail_write(metadata, json_path, markdown_path) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(grm, "write_outputs", fail_write)

    exit_code = grm.main(
        [
            "--json",
            str(tmp_path / "metadata.json"),
            "--markdown",
            str(tmp_path / "metadata.md"),
        ]
    )

    assert exit_code == 1
