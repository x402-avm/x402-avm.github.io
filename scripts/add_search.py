#!/usr/bin/env python3
"""Prepare the exported Mintlify site for Pagefind search (idempotent).

- marks the article container (#content-area) with data-pagefind-body, and the
  prev/next pagination and the Copy page menu with data-pagefind-ignore, so nav, sidebar, TOC and footer
  are not indexed;
- copies assets/search.js and assets/search.css into <site>/assets/;
- injects the stylesheet and script into every HTML page.

Run after build_agent_files.py and before `npx pagefind@1.6.0 --site <site>`.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = "<!-- x402-avm-search -->"
INJECT = (
    f'{MARK}<link rel="stylesheet" href="/assets/search.css">'
    '<script src="/assets/search.js" defer></script>'
)


def add_attr(content: str, pattern: str, attr: str, count: int = 0) -> str:
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        return tag if attr in tag else tag[:-1] + f" {attr}>"
    return re.sub(pattern, repl, content, count=count)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    args = ap.parse_args()
    site = Path(args.site)
    if not (site / "index.html").is_file():
        sys.exit(f"{site} does not look like an exported site (no index.html)")

    (site / "assets").mkdir(exist_ok=True)
    for name in ("search.js", "search.css"):
        shutil.copyfile(ROOT / "assets" / name, site / "assets" / name)

    indexed = 0
    for f in site.rglob("*.html"):
        rel = f.relative_to(site).as_posix()
        text = f.read_text(encoding="utf-8")
        orig = text
        # site/index/index.html is a duplicate of the home page; keep it out of the index.
        if rel != "index/index.html":
            text = add_attr(text, r'<[a-z]+\b[^>]*\bid="content-area"[^>]*>', "data-pagefind-body", count=1)
            for ident in ("pagination", "page-context-menu"):
                text = add_attr(text, rf'<[a-z]+\b[^>]*\bid="{ident}"[^>]*>', "data-pagefind-ignore")
            if "data-pagefind-body" in text:
                indexed += 1
        if MARK not in text and "</head>" in text:
            text = text.replace("</head>", INJECT + "</head>", 1)
        if text != orig:
            f.write_text(text, encoding="utf-8")
    print(f"search: marked {indexed} pages for indexing, injected search assets into {site}")


if __name__ == "__main__":
    main()
