# Web keygen

Browser front end for the keygen, deployed to
<https://micense.github.io/pkey2009/>. The checksum and encoding are a small
JS port of `keygen.py` (`src/lib/keygen.js`); everything runs locally, with no
network calls for generation.

Three features, mirroring the CLI:

- **Generate** — pick a product (curated list in `src/data/skus.js`) and mint
  keys, with one-click copy.
- **Decode** — split a key into its fields and check the checksum.
- **Catalog** — browse/search the full `sku_catalog.json` (like
  `pkey2009 list`), with a per-row _gen_. Loaded on demand from `res/`.

```bash
pnpm install
pnpm dev      # http://localhost:4321/pkey2009/
pnpm build    # writes keygen/web/dist/
pnpm lint     # prettier --check (pnpm format to fix)
```

## Catalog data (`res/`)

The catalog browser fetches `res/sku_catalog.json`. That file lives at the
**repository root**, and CI (`.github/workflows/pages.yml`) copies `res/` into
the published site. For local work on the catalog, stage it once:

```bash
cp -r ../../res public/res    # gitignored; Astro serves public/ verbatim
```

Deployment is handled by `.github/workflows/pages.yml` (GitHub Pages).
