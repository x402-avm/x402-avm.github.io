# AGENTS.md

Guidance for AI coding agents (and people) editing the x402-avm documentation site. The site is a Mintlify project exported to static files and served by GitHub Pages at https://x402-avm.github.io.

## Setup

- Node.js 20.17 or newer (not 25). No `npm install` is needed: the CLI runs with `npx -y mint@4.3.63`.
- Python 3.10+ for the scripts in `scripts/`; `pip install griffe` for the Python reference generator.
- For regeneration, check out the package repositories next to this one: `../ai-economy-sdk`, `../x402-algorand`, `../x402-avm-js`, `../examples`.

## Commands

```bash
npx -y mint@4.3.63 dev            # preview at http://localhost:3000
npx -y mint@4.3.63 broken-links   # must print "no broken links found"
npx -y mint@4.3.63 validate       # strict build, must pass
npx -y mint@4.3.63 export         # static export (export.zip), as deployed

python3 scripts/gen_python_reference.py --ai-economy-sdk ../ai-economy-sdk --x402-algorand ../x402-algorand
python3 scripts/gen_js_reference.py --source ../x402-avm-js/src/index.ts
python3 scripts/sync_examples.py --examples ../examples [--check]
python3 scripts/build_agent_files.py --site site    # after unzipping export.zip into site/
```

## Editing rules

1. **Never invent facts.** Every API name, parameter, default, error code, output and number must come from the package source, the examples repository or an existing page. Check the source before adding a claim. If something is not verified, say so on the page or leave it out.
2. **Do not edit generated files by hand.** `reference/python/**` and `reference/js/**` are generated; change the docstring or TSDoc in the package repository and re-run the generator. The navigation groups `ai-economy-sdk`, `x402-algorand` and `x402-avm-js` of the "API reference" tab in `docs.json` are rewritten by the generators.
3. **Examples are inlined, not copied.** Content between `{/* example: <path> */}` and `{/* /example */}` is written by `scripts/sync_examples.py`. To show an example, add the two markers and run the script.
4. **Pages are MDX.** Every page has `title` and `description` frontmatter. No `#` heading in the body. Internal links are root-relative without extension (`/build/pay-from-python`). Escape `{`, `}` and `<` in prose. Use the built-in components (Steps, Tabs, CodeGroup, Card, Columns, Note, Warning, ParamField, ResponseField, AccordionGroup); icons come from Lucide.
5. **New pages** must be added to `navigation` in `docs.json`, or they are not published in the sidebar, `llms.txt` or `sitemap.xml`. **Moved or deleted pages** must be added to `scripts/redirects.json` and to `redirects` in `docs.json`, so old URLs keep working.
6. **Style:** plain, precise, task-oriented. No marketing terms, no emojis. Amounts in base units with the unit named (microALGO, USDC base units). Network ids in CAIP-2 form (`algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k`).
7. **Never commit** `export.zip`, `site/`, private keys, mnemonics or tokens.
8. **One home per concept.** The payment flow, atomic group, settle-on-success, replay protection, identity and passes are explained in `how-it-works.mdx`; networks and CAIP-2 ids in `production/networks.mdx`; MainNet and USDC in `production/mainnet.mdx`; the threat model in `production/security.mdx`. Elsewhere, write one sentence and link there.
9. **Voice.** Second person, short sentences. Open each page with what the reader will have at the end or when they need the page. Code first, then the explanation.

## Before you finish

- `npx -y mint@4.3.63 broken-links` reports no broken links.
- `npx -y mint@4.3.63 validate` passes.
- `python3 scripts/sync_examples.py --examples ../examples --check` passes if you touched examples.
- If you changed `scripts/build_agent_files.py`, run the export and check `site/llms.txt`, `site/llms-full.txt` and a few `site/<page>.md` files.
- After an export: `python3 scripts/add_redirects.py --site site` and `python3 scripts/check_site_links.py --site site` both succeed.

## Deployment

Pushing to `main` runs `.github/workflows/deploy.yml`: link check, export, unpack to `site/`, `.nojekyll`, `build_agent_files.py`, `add_search.py`, `add_redirects.py`, `check_site_links.py`, Pagefind, then GitHub Pages deploy. Pull requests run `.github/workflows/ci.yml`. Keep the pinned CLI version (`mint@4.3.63`) the same in both workflows, `README.md` and this file.
