#!/usr/bin/env python3
"""Write a redirect stub for every page that moved (idempotent).

The site is a static export served by GitHub Pages, which ignores the ``redirects``
of ``docs.json``. For every old path in ``scripts/redirects.json`` this script writes
``<site>/<old path>/index.html`` (the layout ``mint export`` uses for pages): a small
HTML page with a ``<meta http-equiv="refresh">``, a ``rel=canonical`` link and a
script that calls ``location.replace``. The script keeps old anchors working:

- an old heading id listed under ``anchors`` goes to its new home;
- any other ``#id`` that exists as a heading on the target page is kept;
- anything else lands on the default target.

It also writes ``<old path>.md`` pointing to the new Markdown page, because every
page used to be published as Markdown too.

The redirect targets are checked against the exported site: a target page or
heading that does not exist makes the script fail.

Usage
-----
    python scripts/add_redirects.py --site site [--base-url https://x402-avm.github.io]

Run it after ``build_agent_files.py`` and ``add_search.py`` and before Pagefind
(the stubs have no ``data-pagefind-body``, so they are not indexed).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://x402-avm.github.io"
HEADING_ID = re.compile(r'<h[1-6]\b[^>]*\bid="([^"]+)"')

STUB = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved: {title}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={target}">
<script>
(function () {{
  var anchors = {anchors};
  var ids = {ids};
  var h = decodeURIComponent((location.hash || "").slice(1));
  var dest = {target_js};
  if (h && anchors[h]) dest = anchors[h];
  else if (h && ids.indexOf(h) !== -1) dest = {page_js} + "#" + h;
  location.replace(dest);
}})();
</script>
</head>
<body>
<p>This page moved to <a href="{target}">{canonical}</a>.</p>
</body>
</html>
"""


def page_file(site: Path, path: str) -> Path:
    path = path.strip("/")
    return site / "index.html" if not path else site / path / "index.html"


def heading_ids(site: Path, path: str, cache: dict[str, list[str]]) -> list[str]:
    if path not in cache:
        f = page_file(site, path)
        if not f.is_file():
            sys.exit(f"redirect target {path} does not exist in {site}")
        cache[path] = sorted(set(HEADING_ID.findall(f.read_text(encoding="utf-8"))))
    return cache[path]


def check(site: Path, url: str, cache: dict[str, list[str]]) -> None:
    page, _, anchor = url.partition("#")
    ids = heading_ids(site, page, cache)
    if anchor and anchor not in ids:
        sys.exit(f"redirect target {url}: no heading #{anchor} on {page}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    site = Path(args.site)
    base = args.base_url.rstrip("/")
    if not (site / "index.html").is_file():
        sys.exit(f"{site} does not look like an exported site (no index.html)")

    redirects = json.loads((ROOT / "scripts" / "redirects.json").read_text())["redirects"]
    cache: dict[str, list[str]] = {}
    for old, spec in redirects.items():
        target = spec["to"]
        check(site, target, cache)
        for url in spec.get("anchors", {}).values():
            check(site, url, cache)
        page = target.split("#")[0]
        stub = page_file(site, old)
        if stub.is_file() and "Moved:" not in stub.read_text(encoding="utf-8"):
            sys.exit(f"{old} is both a redirect source and a real page; remove it from redirects.json")
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text(
            STUB.format(
                title=html.escape(page),
                canonical=html.escape(base + target),
                target=html.escape(target),
                anchors=json.dumps(spec.get("anchors", {})),
                ids=json.dumps(heading_ids(site, page, cache)),
                target_js=json.dumps(target),
                page_js=json.dumps(page),
            ),
            encoding="utf-8",
        )
        md_target = f"{base}{page}.md" if page != "/" else f"{base}/index.md"
        (site / f"{old.strip('/')}.md").write_text(
            f"# Moved\n\nThis page moved to {base}{target} (Markdown: {md_target}).\n", encoding="utf-8"
        )
    print(f"redirects: wrote {len(redirects)} stubs into {site}")


if __name__ == "__main__":
    main()
