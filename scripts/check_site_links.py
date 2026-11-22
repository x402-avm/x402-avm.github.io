#!/usr/bin/env python3
"""Check every internal link of the exported site (HTML pages and llms.txt).

For each ``href="/..."`` in every HTML file, and each site URL in ``llms.txt`` and
``llms-full.txt``, the target must exist as a file, as ``<path>/index.html`` or as
``<path>.html``. A ``#fragment`` pointing at an HTML page must match an ``id`` on that
page; redirect stubs written by ``add_redirects.py`` resolve anchors themselves and
are checked there. Exits 1 and lists the broken links if any.

Usage
-----
    python scripts/check_site_links.py --site site [--base-url https://x402-avm.github.io]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

DEFAULT_BASE = "https://x402-avm.github.io"
HREF = re.compile(r'\bhref="(/[^"]*)"')
ID = re.compile(r'\bid="([^"]+)"')
SKIP = ("/_mintlify/", "/_next/", "/pagefind/")


def resolve(site: Path, path: str) -> Path | None:
    rel = unquote(path).strip("/")
    for cand in (site / rel, site / rel / "index.html", site / f"{rel}.html"):
        if cand.is_file():
            return cand
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    site = Path(args.site)
    base = args.base_url.rstrip("/")
    ids_cache: dict[Path, set[str]] = {}
    broken: dict[str, set[str]] = defaultdict(set)
    checked = 0

    def check(src: str, link: str) -> None:
        nonlocal checked
        if link.startswith(SKIP) or link.startswith("//"):
            return
        path, _, frag = link.partition("#")
        path = path.split("?")[0] or "/"
        checked += 1
        target = resolve(site, path)
        if target is None:
            broken[src].add(link)
            return
        if frag and target.suffix == ".html":
            text = target.read_text(encoding="utf-8", errors="replace")
            if "Moved:" in text and 'http-equiv="refresh"' in text:
                return
            if target not in ids_cache:
                ids_cache[target] = set(ID.findall(text))
            if unquote(frag) not in ids_cache[target]:
                broken[src].add(link)

    for f in sorted(site.rglob("*.html")):
        src = f.relative_to(site).as_posix()
        for link in HREF.findall(f.read_text(encoding="utf-8", errors="replace")):
            check(src, link.replace("&amp;", "&"))
    for name in ("llms.txt", "llms-full.txt"):
        f = site / name
        if f.is_file():
            for m in re.finditer(re.escape(base) + r"(/[^\s)>\"'`]*)", f.read_text(encoding="utf-8")):
                check(name, m.group(1).rstrip(".,"))

    if broken:
        for src, links in sorted(broken.items()):
            print(f"{src}:")
            for link in sorted(links):
                print(f"  {link}")
        sys.exit(f"{sum(map(len, broken.values()))} broken internal links ({checked} checked)")
    print(f"links: {checked} internal links checked, none broken")


if __name__ == "__main__":
    main()
