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
cd site && node serve.js                         # http://localhost:3000
```

`export.zip` and `site/` are ignored by git; never commit them.

## Structure

| Path | Contents |
|---|---|
| `docs.json` | Site configuration: theme, colours, navbar, footer, navigation |
| `index.mdx`, `quickstart.mdx`, `how-it-works.mdx`, `installation.mdx`, `networks.mdx`, `glossary.mdx` | Get started |
| `guides/networks/` | LocalNet, TestNet and MainNet guides |
| `ai-economy-sdk/`, `x402-algorand/`, `x402-avm-js/` | Guides per package |
| `tutorials/` | End-to-end tutorials |
| `agents/` | For AI agents: paying for tools, guardrails, docs for AI tools, AGENTS.md files |
| `reference/python/` | Python API reference, **generated** |
| `reference/js/` | JavaScript API reference, **generated** |
| `reference/x402/` | Summary of the official x402 SDK classes (hand-written) |
| `resources/` | Security, troubleshooting, error codes, FAQ, changelog |
| `logo/`, `favicon.svg` | Wordmark (light and dark) and icon |
| `scripts/` | Generators and the post-export step (not published) |
| `.github/workflows/` | `deploy.yml` (push to `main`) and `ci.yml` (pull requests) |

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

- `gen_python_reference.py` writes one page per public object (listed in its `PACKAGES` table) under `reference/python/<package>/`, an overview page per package, and updates the `ai-economy-sdk` and `x402-algorand` groups of the "API reference" tab in `docs.json`. To document a new public object, add it to `PACKAGES`.
- `gen_js_reference.py` writes one page per documented export of `src/index.ts` under `reference/js/` and updates the `x402-avm-js` group. It fails if an export has no TSDoc or is missing from its `CATEGORIES` table. Interface property descriptions come from `scripts/js_reference_overlay.json`.

## Refresh the inlined examples

Pages embed files from [x402-avm/examples](https://github.com/x402-avm/examples) between `{/* example: <path> */}` and `{/* /example */}` markers. After the examples change:

```bash
python3 scripts/sync_examples.py --examples ../examples          # rewrite the blocks
python3 scripts/sync_examples.py --examples ../examples --check  # fails if a block is stale
```

Marker paths are relative to the root of the examples repository (`localnet/...`, `testnet/...`, `mainnet/...`); the files are copied verbatim.

## Deployment

`deploy.yml` runs on every push to `main` and on manual dispatch: it checks links, runs `mint export`, unpacks the archive into `site/`, adds `.nojekyll`, runs `scripts/build_agent_files.py` (Markdown version of every page, `llms.txt`, `llms-full.txt`, `sitemap.xml`), and deploys `site/` with `actions/deploy-pages`. In the repository settings, set **Pages > Source** to **GitHub Actions**.

`ci.yml` runs the link check, the export and the post-export step on pull requests.

The Mintlify CLI version is pinned (`mint@4.3.63`) in both workflows and in these instructions; update all of them together.

## Licence

Documentation content: MIT, see [LICENSE](LICENSE). The packages have their own licences: `ai-economy-sdk` and `x402-avm-js` MIT, `x402-algorand` Apache-2.0. The Mintlify CLI is licensed separately by Mintlify (Elastic License 2.0).
