"""Check links and anchors in the built site.

The strict build validates links written in ``docs/``. It does not validate
links that arrive through snippets, so this script inspects the generated
HTML instead.

Usage:
    python scripts/check_built_site.py
    python scripts/check_built_site.py --site-dir site
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

EXTERNAL_SCHEMES = {
    "http",
    "https",
    "mailto",
    "tel",
    "data",
    "javascript",
}


class PageParser(HTMLParser):
    """Collect links, asset references, and anchors from one page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.assets: list[str] = []
        self.anchors: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        anchor_id = values.get("id")
        if anchor_id:
            self.anchors.add(anchor_id)
        if tag == "a":
            if values.get("name"):
                self.anchors.add(values["name"])
            if values.get("href"):
                self.links.append(values["href"])
        if tag in {
            "img",
            "script",
            "source",
            "iframe",
            "video",
            "audio",
            "embed",
        } and values.get("src"):
            self.assets.append(values["src"])
        if tag in {"img", "source"} and values.get("srcset"):
            for candidate in values["srcset"].split(","):
                asset = candidate.strip().split(" ")[0]
                if asset:
                    self.assets.append(asset)
        if tag == "object" and values.get("data"):
            self.assets.append(values["data"])
        if tag == "link" and values.get("href"):
            rel = (values.get("rel") or "").lower()
            if "stylesheet" in rel or "icon" in rel:
                self.assets.append(values["href"])


def load_config(config_path: Path) -> tuple[str, str]:
    """Return the site URL and configured site directory."""

    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    project = config.get("project", {})
    return project.get("site_url", ""), project.get("site_dir", "site")


def url_for(relative: str) -> str:
    """Return the URL path Zensical gives a built page."""

    if relative.endswith("index.html"):
        return "/" + relative[: -len("index.html")]
    return "/" + relative


def target_file(site_dir: Path, path: str) -> Path | None:
    """Map a URL path to a built file, trying directory and file forms."""

    clean = path.lstrip("/")
    candidates = ["index.html"] if not clean else [clean]
    if clean and not clean.endswith("/"):
        candidates.extend([clean + ".html", clean + "/index.html"])
    elif clean:
        candidates.append(clean + "index.html")
    for candidate in candidates:
        file = site_dir / candidate
        if file.is_file():
            return file
    return None


def strip_base(path: str, base_path: str) -> str:
    """Remove the GitHub Pages base path from an absolute URL path."""

    if base_path and path.startswith(base_path):
        return path[len(base_path) :]
    return path.lstrip("/")


def outside_base(path: str, base_path: str) -> bool:
    """Return whether an absolute path escapes the published base path."""

    return bool(
        base_path
        and base_path != "/"
        and path.startswith("/")
        and not path.startswith(base_path)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("zensical.toml"),
        help="Zensical configuration file.",
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=None,
        help="Built site directory. Overrides the configuration value.",
    )
    args = parser.parse_args()

    site_url, configured_dir = load_config(args.config)
    site_dir = args.site_dir or args.config.parent / configured_dir
    base_path = urlparse(site_url).path

    pages = {
        page.relative_to(site_dir).as_posix(): page
        for page in site_dir.rglob("*.html")
    }
    if not pages:
        print(f"No HTML files found in {site_dir}", file=sys.stderr)
        return 1

    parsed = {name: PageParser() for name in pages}
    for name, page in pages.items():
        parsed[name].feed(page.read_text(encoding="utf-8"))

    broken: list[tuple[str, str, str]] = []
    checked = 0

    for page_name, page_parser in parsed.items():
        current_url = url_for(page_name)
        for href in page_parser.links:
            checked += 1
            if href.startswith("#"):
                target_path = url_for(page_name)
                fragment = href[1:]
            else:
                parsed_href = urlparse(href)
                if parsed_href.scheme.lower() in EXTERNAL_SCHEMES:
                    continue
                if parsed_href.netloc or not parsed_href.path:
                    continue
                if parsed_href.path.startswith("/"):
                    if outside_base(parsed_href.path, base_path):
                        broken.append((page_name, href, parsed_href.path))
                        continue
                    target_path = strip_base(parsed_href.path, base_path)
                    target_path = "/" + target_path.lstrip("/")
                else:
                    target_path = urljoin(current_url, parsed_href.path)
                fragment = parsed_href.fragment

            file = target_file(site_dir, target_path)
            if file is None:
                broken.append((page_name, href, target_path))
                continue
            if fragment:
                target_name = file.relative_to(site_dir).as_posix()
                if target_name not in parsed:
                    broken.append((page_name, href, target_name))
                    continue
                target_ids = parsed[target_name].anchors
                if unquote(fragment) not in target_ids:
                    broken.append(
                        (page_name, href, f"{target_name}#{fragment}")
                    )

        for asset in page_parser.assets:
            checked += 1
            parsed_asset = urlparse(asset)
            if parsed_asset.scheme.lower() in EXTERNAL_SCHEMES:
                continue
            if parsed_asset.netloc or not parsed_asset.path:
                continue
            if parsed_asset.path.startswith("/"):
                if outside_base(parsed_asset.path, base_path):
                    broken.append((page_name, asset, parsed_asset.path))
                    continue
                asset_path = strip_base(parsed_asset.path, base_path)
            else:
                asset_path = urljoin(
                    current_url, parsed_asset.path
                ).lstrip("/")
            if not (site_dir / asset_path).is_file():
                broken.append((page_name, asset, asset_path))

    print(f"Checked {len(pages)} pages and {checked} references.")
    if broken:
        print(f"Broken references: {len(broken)}")
        for page_name, href, target in broken:
            print(f"  {page_name}: {href} -> {target}")
        return 1
    print("All local links, anchors, and assets resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
