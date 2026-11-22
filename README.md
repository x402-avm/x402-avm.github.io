# x402-avm documentation

Source of the documentation site for [ai-economy-sdk](https://github.com/x402-avm/ai-economy-sdk), [x402-algorand](https://github.com/x402-avm/x402-algorand) and [x402-avm-js](https://github.com/x402-avm/x402-avm-js), published at **https://x402-avm.github.io**.

The site is a [Mintlify](https://mintlify.com) project. It is exported to static files with the Mintlify CLI and served by GitHub Pages from this repository (`x402-avm/x402-avm.github.io`), so it lives at the domain root, which the export requires.

## Run the docs locally

Requirements: Node.js 20.17 or newer (not 25), and Python 3.10+ for the scripts.

```bash
npx -y mint@4.3.63 dev            # preview at http://localhost:3000
npx -y mint@4.3.63 broken-links   # must report "no broken links found"
npx -y mint@4.3.63 validate       # strict build
```

To check the static site exactly as it is deployed:

```bash
npx -y mint@4.3.63 export                       # writes export.zip
rm -rf site && mkdir site && unzip -q export.zip -d site
python3 scripts/build_agent_files.py --site site
python3 scripts/add_search.py --site site
python3 scripts/add_redirects.py --site site     # stubs for moved pages
python3 scripts/check_site_links.py --site site  # every internal link and anchor
npx -y pagefind@1.6.0 --site site
cd site && node serve.js                         # http://localhost:3000
```

`export.zip` and `site/` are ignored by git; never commit them.

## Structure

| Path | Contents |
|---|---|
| `docs.json` | Site configuration: theme, colours, navbar, footer, navigation, redirects |
| `index.mdx`, `quickstart.mdx`, `how-it-works.mdx` | Start here. `how-it-works.mdx` is the one place the payment flow, the atomic group, settle-on-success, replay protection, identity and passes are explained |
| `build/` | Task guides: sell MCP tools, pricing and passes, paywall an HTTP API, pay from Python / the browser / Node.js, AI agents, identity, facilitator |
| `production/` | Networks (LocalNet, TestNet, private), going to MainNet (USDC, fee payer, checklist), security |
| `reference/index.mdx`, `reference/packages.mdx`, `reference/protocol/`, `reference/errors.mdx` | Packages and versions, AVM exact scheme, HTTP 402 headers, error codes |
| `reference/python/` | Python API reference, **generated** |
| `reference/js/` | JavaScript API reference, **generated** |
| `reference/x402/` | Summary of the official x402 SDK classes (hand-written) |
| `resources/` | Troubleshooting, FAQ, glossary, changelog, docs for AI tools |
| `logo/`, `favicon.svg` | Wordmark (light and dark) and icon |
| `scripts/` | Generators and the post-export step (not published) |
| `.github/workflows/` | `deploy.yml` (push to `main`) and `ci.yml` (pull requests) |

## Moving or deleting a page

Every old URL must keep working. Add the old path to `scripts/redirects.json` with its new target (`to`) and, for headings that moved elsewhere, an `anchors` map; headings with the same id on the target page are matched automatically. Then copy the entries into `redirects` in `docs.json` (destination without the `#anchor`). `add_redirects.py` writes `<old path>/index.html` and `<old path>.md` into the exported site and fails if a target page or heading does not exist.

## Regenerate the API reference

The reference pages are generated from the package sources and committed. Regenerate them whenever a docstring, TSDoc comment or public signature changes. The scripts expect the package repositories as sibling checkouts by default:

```
x402-avm-org/
├── ai-economy-sdk/
├── x402-algorand/
├── x402-avm-js/
├── examples/
└── x402-avm.github.io/   <- this repository
```

```bash
pip install griffe   # static docstring parser; nothing is imported or executed

python3 scripts/gen_python_reference.py --ai-economy-sdk ../ai-economy-sdk --x402-algorand ../x402-algorand
python3 scripts/gen_js_reference.py --source ../x402-avm-js/src/index.ts
npx -y mint@4.3.63 broken-links
```

- `gen_python_reference.py` writes one page per public object (listed in its `PACKAGES` table) under `reference/python/<package>/`, an overview page per package, and updates the `ai-economy-sdk` and `x402-algorand` groups of the "API reference" tab in `docs.json`. To document a new public object, add it to `PACKAGES`. Objects whose docstring has no Examples section can get one from `scripts/python_reference_examples.json`; keep those examples runnable.
- `gen_js_reference.py` writes one page per documented export of `src/index.ts` and `src/errors.ts` under `reference/js/` and updates the `x402-avm-js` group. It fails if an export has no TSDoc or is missing from its `CATEGORIES` table. Interface property descriptions come from `scripts/js_reference_overlay.json`.

## Refresh the inlined examples

Pages embed files from [x402-avm/examples](https://github.com/x402-avm/examples) between `{/* example: <path> */}` and `{/* /example */}` markers. After the examples change:

```bash
python3 scripts/sync_examples.py --examples ../examples          # rewrite the blocks
python3 scripts/sync_examples.py --examples ../examples --check  # fails if a block is stale
```

Marker paths are relative to the root of the examples repository (`localnet/...`, `testnet/...`, `mainnet/...`); the files are copied verbatim.

## Deployment

`deploy.yml` runs on every push to `main` and on manual dispatch: it checks links, runs `mint export`, unpacks the archive into `site/`, adds `.nojekyll`, runs `scripts/build_agent_files.py` (Markdown version of every page, `llms.txt`, `llms-full.txt`, `sitemap.xml`), `scripts/add_search.py`, `scripts/add_redirects.py` (a redirect stub for every moved page, from `scripts/redirects.json`), `scripts/check_site_links.py` and Pagefind, and deploys `site/` with `actions/deploy-pages`. In the repository settings, set **Pages > Source** to **GitHub Actions**.

`ci.yml` runs the link check, the export and the post-export step on pull requests.

The Mintlify CLI version is pinned (`mint@4.3.63`) in both workflows and in these instructions; update all of them together.

## Licence

Documentation content: MIT, see [LICENSE](LICENSE). The packages have their own licences: `ai-economy-sdk` and `x402-avm-js` MIT, `x402-algorand` Apache-2.0. The Mintlify CLI is licensed separately by Mintlify (Elastic License 2.0).
