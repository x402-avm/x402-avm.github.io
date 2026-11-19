#!/usr/bin/env python3
"""Inline example files from the x402-avm/examples repository into the MDX pages.

A page marks where an example goes with a pair of MDX comments:

    {/* example: python/sdk_quickstart_server.py */}
    {/* /example */}

Everything between the two markers is replaced by a code block holding the file's
current content and a link to the file on GitHub. Run the script after the examples
change, then commit the updated pages.

Usage
-----
    python scripts/sync_examples.py --examples ../examples          # rewrite pages
    python scripts/sync_examples.py --examples ../examples --check  # exit 1 if a page is stale

Paths are relative to the root of the examples repository (``localnet/``,
``testnet/``, ``mainnet/``). The files are copied verbatim.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/x402-avm/examples/blob/main"
BLOCK = re.compile(
    r"(?P<indent>^[ \t]*)(?P<open>\{/\* example: (?P<path>[^ ]+) \*/\})(?P<body>[\s\S]*?)(?P<close>\{/\* /example \*/\})",
    re.MULTILINE,
)
LANG = {".py": "python", ".mjs": "javascript", ".js": "javascript", ".ts": "typescript", ".html": "html"}


def render(rel: str, examples: Path, indent: str = "") -> str:
    src = examples / rel
    if not src.is_file():
        sys.exit(f"example not found: {src}")
    code = src.read_text().rstrip("\n")
    lang = LANG.get(src.suffix, "text")
    fence = "````" if "```" in code else "```"
    opts = " expandable" if code.count("\n") > 45 else ""
    block = (
        f"{fence}{lang} {rel}{opts}\n{code}\n{fence}\n\n"
        f"<sub>Source: [examples/{rel}]({REPO_URL}/{rel})</sub>"
    )
    # Indent like the marker so the block stays inside an enclosing component (Step, Tab).
    body = "\n".join((indent + line) if line else "" for line in block.split("\n"))
    return f"\n\n{body}\n\n{indent}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--examples", default=str(SITE.parent / "examples"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    examples = Path(args.examples)
    stale, count = [], 0
    for page in sorted(SITE.rglob("*.mdx")):
        if "node_modules" in page.parts:
            continue
        text = page.read_text()
        new = BLOCK.sub(
            lambda m: m.group("indent") + m.group("open") + render(m.group("path"), examples, m.group("indent")) + m.group("close"),
            text,
        )
        count += len(BLOCK.findall(text))
        if new != text:
            stale.append(page.relative_to(SITE))
            if not args.check:
                page.write_text(new)
    if args.check and stale:
        sys.exit("stale examples in: " + ", ".join(map(str, stale)))
    print(f"{count} example blocks; {'stale' if args.check else 'updated'}: {len(stale)} pages")


if __name__ == "__main__":
    main()
