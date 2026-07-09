# Data Safety

Carbon Scenario Explorer is designed so a public deployment can **never** expose internal,
confidential, or proprietary data.

## What ships in this repository

All data under `backend/data/` is **synthetic, anonymized, and demo-safe**:

- **Products** are generic placeholders: `Smartphone A`, `Smartphone Pro`, `Tablet B`,
  `Laptop C`, `Wearable D`, `Sample Product A/B`.
- **Materials** are generic labels: `Alloy-A`…`Alloy-H`, `Cast-A/B`, `Polymer-A/B/C`.
- **Manufacturing regions** are neutral: `Region A/B/C`, `100% renewables`.
- **PMF sample files** (`backend/data/pmf/*.csv`) follow the PMF schema shape with synthetic
  masses and generic component names — no real BOMs.
- **Process constants** (`supporting_data.csv`) are illustrative values.

No Apple / internal / confidential / proprietary strings, real product identifiers, real vendor
names, or absolute local paths are present in the tracked source or data.

## Guardrails

### Data-mode separation

- `PUBLIC_DEMO_MODE=true` (set on the public deployment) and `DATA_MODE=external` force the app
  into demo-safe mode. `PUBLIC_DEMO_MODE=true` forces `DATA_MODE=external` regardless of any other
  setting.
- The current mode is surfaced at `GET /api/config` and shown as a visible badge in the UI.

### Dataset path guardrail

`require_public_safe_dataset()` in `backend/app/config.py` runs before any dataset is loaded
(alloy table, supporting data, PMF directory). In public/external mode it **raises
`UnsafeDatasetError`** if a path:

- resolves outside the bundled `backend/data/` directory, or
- contains any of: `internal`, `confidential`, `proprietary`, `private`, `restricted`.

This prevents a stray environment variable or misconfiguration from pointing the public
deployment at non-public data.

### Read-only / no-upload

- The public demo does **not** expose a file-upload or arbitrary-import endpoint; data is loaded
  only from the vetted bundled directory.
- Scenario persistence degrades gracefully to in-memory on read-only serverless filesystems, so
  no writable data path is required in production.

## Provenance is retained as source-type metadata

Field-level provenance (source type + confidence) is preserved in demo mode, but it refers to
**demo-safe source categories** (`pmf_imported`, `pmf_inferred`, `class_default`, `model_default`)
against synthetic data — never confidential records.

## Unsupported categories are marked, not faked

Components in categories without a validated calculator are labeled **approximate** or
**unsupported** rather than being silently estimated with false precision. See the model-validity
system in the README.

## Not an official or certified report

This tool provides **scenario estimates for exploratory engineering analysis**. It is not a
certified LCA, regulatory carbon accounting report, or official product environmental report, and
it is **not** an official Apple tool and does not use confidential Apple data.
