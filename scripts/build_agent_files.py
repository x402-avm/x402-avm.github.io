#!/usr/bin/env python3
"""Write the machine-readable files of the exported site.

`mint export` produces the HTML site and an ``llms.txt``, but no Markdown version of
the pages, no ``llms-full.txt`` and no ``sitemap.xml``, although every exported page
links to its ``.md`` version and to ``/sitemap.xml``. This script fills the gap. It
reads ``docs.json`` and the MDX sources, and writes into the exported site folder:

- ``<page>.md`` for every page in the navigation (``index.md`` for the home page),
- ``llms.txt``: an index of all pages, grouped as in the navigation, linking to the
  ``.md`` files (replaces the export's simpler ``llms.txt``),
- ``llms-full.txt``: every page's Markdown, in navigation order,
- ``sitemap.xml``.

Usage
-----
    python scripts/build_agent_files.py --site site [--base-url https://x402-avm.github.io]

Only the Python standard library is used. The MDX-to-Markdown conversion is a light
transformation of the components used on this site; code blocks are kept verbatim.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

SITE_SRC = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://x402-avm.github.io"

ATTR = re.compile(r'(\w+)(?:=(?:"([^"]*)"|\{([^}]*)\}))?')
FENCE = re.compile(r"^(\s*)(`{3,})(.*)$")


def attrs(tag: str) -> dict[str, str]:
    inner = re.sub(r"^<\w+\s*|/?>$", "", tag.strip())
    out = {}
    for m in ATTR.finditer(inner):
        out[m.group(1)] = html.unescape(m.group(2) if m.group(2) is not None else (m.group(3) or "true"))
    return out


def nav_pages(docs: dict) -> list[tuple[str, str, str]]:
    """(tab, group path, page) in navigation order."""
    out: list[tuple[str, str, str]] = []

    def walk(node, tab: str, group: str) -> None:
        if isinstance(node, str):
            out.append((tab, group, node))
        elif isinstance(node, dict):
            g = node.get("group")
            path = f"{group} / {g}" if group and g else (g or group)
            for p in node.get("pages", []):
                walk(p, tab, path)
            for key in ("groups",):
                for sub in node.get(key, []):
                    walk(sub, tab, path)

    for tab in docs["navigation"]["tabs"]:
        for grp in tab.get("groups", []):
            walk(grp, tab["tab"], "")
    return out


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n([\s\S]*?)\n---\n", text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith('"'):
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    v = v.strip('"')
            meta[k.strip()] = v
    return meta, text[m.end():]


def field_line(tag: str) -> str:
    a = attrs(tag)
    name = a.get("body") or a.get("query") or a.get("path") or a.get("header") or a.get("name") or ""
    bits = []
    if a.get("type"):
        bits.append(f"`{a['type']}`")
    if "required" in a:
        bits.append("required")
    if a.get("default") is not None and "default" in a:
        bits.append(f"default `{a['default']}`")
    meta = f" ({', '.join(bits)})" if bits else ""
    return f"- `{name}`{meta}:"


def absolutize(line: str, base: str) -> str:
    return re.sub(r"\]\((/[^)\s]*)\)", lambda m: f"]({base}{m.group(1)})", line)


def mdx_to_md(body: str, base: str) -> str:
    body = re.sub(r"\{/\*[\s\S]*?\*/\}", "", body)
    out: list[str] = []
    fence_indent: int | None = None
    fence_mark = ""
    for raw in body.splitlines():
        m = FENCE.match(raw)
        if fence_indent is not None:
            if m and m.group(2).startswith(fence_mark) and not m.group(3).strip():
                out.append(fence_mark)
                fence_indent = None
                continue
            strip = min(fence_indent, len(raw) - len(raw.lstrip(" ")))
            out.append(raw[strip:])
            continue
        if m:
            if out and out[-1] != "":
                out.append("")
            fence_indent = len(m.group(1))
            fence_mark = m.group(2)
            info = m.group(3).strip().split()
            out.append(fence_mark + (info[0] if info else ""))
            continue
        line = raw.strip()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        # Components
        if re.match(r"^<(ParamField|ResponseField)\b", line):
            text = field_line(re.match(r"^<[^>]*>", line).group(0))
            rest = re.sub(r"^<[^>]*>", "", line).replace("</ParamField>", "").replace("</ResponseField>", "").strip()
            out.append(f"{text} {rest}".rstrip())
            continue
        if re.match(r"^</(ParamField|ResponseField)>$", line):
            continue
        cm = re.match(r"^<Card\b([^>]*)>(.*?)(</Card>)?$", line)
        if cm:
            a = attrs(f"<Card {cm.group(1)}>")
            href = a.get("href", "")
            if href.startswith("/"):
                href = f"{base}{href}.md" if not href.endswith(".md") else f"{base}{href}"
            text = cm.group(2).strip()
            out.append(f"- [{a.get('title', '')}]({href})" + (f": {text}" if text else ""))
            continue
        for comp, prefix in (("Step", "### "), ("Accordion", "### "), ("Tab", "**")):
            sm = re.match(rf"^<{comp}\b([^>]*)>$", line)
            if sm:
                title = attrs(f"<{comp} {sm.group(1)}>").get("title", "")
                out.extend(["", f"{prefix}{title}**" if prefix == "**" else f"{prefix}{title}", ""])
                break
        else:
            um = re.match(r"^<Update\b([^>]*)>$", line)
            if um:
                a = attrs(f"<Update {um.group(1)}>")
                out.extend(["", f"## {a.get('label', '')}" + (f" ({a['description']})" if a.get("description") else ""), ""])
                continue
            cal = re.match(r"^<(Note|Warning|Tip|Info|Check|Danger)>(.*?)(</\1>)?$", line)
            if cal:
                out.append(f"> **{cal.group(1)}:** {cal.group(2).strip()}".rstrip())
                continue
            if re.match(r"^</?(Columns|Column|CodeGroup|Steps|Step|Tabs|Tab|AccordionGroup|Accordion|Expandable|Update|Note|Warning|Tip|Info|Check|Danger|Card|Frame)\b[^>]*>$", line):
                continue
            line = re.sub(r"</?sub>", "", line)
            line = html.unescape(line)
            out.append(absolutize(line, base))
            continue
        continue
    # Collapse runs of blank lines produced by removed components, outside code only.
    cleaned: list[str] = []
    in_code = False
    for line in out:
        if line.startswith("```"):
            # An opening fence may carry a language; a closing fence is bare.
            if not in_code:
                in_code = True
            elif line.strip("`") == "":
                in_code = False
        if not in_code and line == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True, help="folder holding the unzipped export")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    site = Path(args.site)
    base = args.base_url.rstrip("/")
    if not (site / "index.html").is_file():
        sys.exit(f"{site} does not look like an exported site (no index.html)")

    docs = json.loads((SITE_SRC / "docs.json").read_text())
    pages = nav_pages(docs)
    seen = set()
    llms = [f"# {docs['name']} documentation", "", f"> {docs.get('description', '')}", ""]
    llms += [
        f"Every page is also available as Markdown at its URL plus `.md`. The full text of all pages is at {base}/llms-full.txt.",
        "",
    ]
    full = [f"# {docs['name']} documentation (full text)", "", f"> {docs.get('description', '')}", ""]
    urls = []
    current_section = None
    for tab, group, page in pages:
        if page in seen:
            continue
        seen.add(page)
        src = SITE_SRC / f"{page}.mdx"
        if not src.is_file():
            sys.exit(f"navigation lists {page} but {src} is missing")
        meta, body = frontmatter(src.read_text())
        title = meta.get("title", page)
        desc = meta.get("description", "")
        md = f"# {title}\n\n" + (f"> {desc}\n\n" if desc else "") + mdx_to_md(body, base)
        md_url = f"{base}/{page}.md"
        html_url = f"{base}/" if page == "index" else f"{base}/{page}"
        out = site / f"{page}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md + f"\nSource: {html_url}\n")
        section = f"{tab}: {group}" if group and group != tab else tab
        if section != current_section:
            llms += ["", f"## {section}", ""]
            current_section = section
        llms.append(f"- [{title}]({md_url})" + (f": {desc}" if desc else ""))
        full += ["", "---", "", f"<!-- {html_url} -->", "", md.strip(), ""]
        urls.append(html_url)

    (site / "llms.txt").write_text("\n".join(llms).replace("\n\n\n", "\n\n") + "\n")
    (site / "llms-full.txt").write_text("\n".join(full) + "\n")
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{xml_escape(u)}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (site / "sitemap.xml").write_text("\n".join(sitemap) + "\n")
    print(f"wrote {len(urls)} Markdown pages, llms.txt, llms-full.txt and sitemap.xml into {site}")


if __name__ == "__main__":
    main()
