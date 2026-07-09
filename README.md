# Carbon Scenario Explorer

Carbon Scenario Explorer is a category-routed **carbon scenario modeling** tool for product
development decisions. It lets users compare how engineering choices — material swaps,
recycled-content changes, source/vendor assumptions, manufacturing processes, packaging design,
and logistics parameters — affect **estimated product carbon intensity** in real time.

The tool is designed for exploratory engineering analysis. **It is not a certified LCA,
regulatory carbon accounting report, or official product environmental report.**

> **Real-time carbon scenario modeling for product development decisions.**
>
> Explore how material choices, recycled content, vendor/source assumptions, manufacturing
> processes, packaging decisions, and logistics parameters affect estimated product carbon
> intensity — before those decisions become locked into a product plan.

---

## Public demo mode

**This public demo uses synthetic and external/demo-safe datasets. It does not include
confidential product data, proprietary PMF records, internal company datasets, or non-public
engineering assumptions.**

The architecture supports separated internal and external data adapters. **This deployment runs
in public demo mode** (external/demo data only). See [DATA_SAFETY.md](DATA_SAFETY.md).

## Why this matters

Many carbon-relevant decisions happen before formal sustainability review: materials,
manufacturing processes, supplier/source assumptions, packaging formats, and logistics choices.
Most carbon impact is shaped upstream, when product teams make those choices. Carbon Scenario
Explorer turns them into live scenario comparisons so teams can see impact while decisions are
still actionable.

**Built for:** product development engineers · engineering managers · hardware program teams ·
environmental product analysts · operations/manufacturing teams · sustainability reviewers ·
technical leaders evaluating tradeoffs.

## What you can change

Material swaps · recycled content · vendor/source assumptions · manufacturing grid/region ·
manufacturing process mix · packaging material mix · shipping/modal split · component mass ·
product-level rollup assumptions.

## What the system returns

Estimated carbon impact · baseline vs. scenario delta (absolute + percent) · process breakdown ·
component contribution · product-level rollup · provenance & confidence per field · model
validity badge · formula/audit trace.

---

## Tech stack

- **Backend**: Python 3.12+ / FastAPI / Pandas
- **Frontend**: React 19 / TypeScript / Vite / Recharts
- **Data**: CSV-based (PMF format for product data; lookup tables for materials and process constants)
- **Deployment**: Local-first, plus a public Vercel demo (see [DEPLOYMENT.md](DEPLOYMENT.md))

## Quickstart (local)

```bash
./start.sh
```

Then open **http://localhost:5173**. This sets up the Python venv and `node_modules`, starts the
backend with a health check, and starts the frontend.

### Manual startup

**Terminal 1 — Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install && npm run dev
```

**Prerequisites:** Python 3.12+, Node.js 22+.

---

## Architecture

### Category-routed calculation engine

The core design principle is **one engine per product category**, not one universal calculator.
Calculations flow through the dispatcher in `backend/app/engine/calculators/__init__.py`, which
routes to a category-specific calculator based on component classification.

```
ScenarioInput + ComponentClass
         ↓
    Category Router
    ├── Enclosure Calculator (mass-based, 11 manufacturing processes)
    ├── Packaging Calculator (material GWP + shipping modal split)
    └── [future] PCB, Textile, Titanium, Transportation calculators
         ↓
    Unified ProcessBreakdown output
         ↓
    Charts / Comparison / Report
```

### Calculator coverage

| Calculator | Category | Unit basis | What it models |
|-----------|----------|-----------|----------------|
| **Enclosure** | Metal structural, polymer housing, hardware | kg (mass) | 11 manufacturing processes: raw material CI, upstream semi-fabrication, forging, stamping, heat treatment, machining, laser, sanding, die casting, injection molding, anodizing |
| **Packaging** | Packaging components | g (mass) | Material GWP lookup (13 packaging materials) + shipping carbon by modal split (air / sea / ground) |

### Model validity system — no false precision

**The tool does not silently produce false precision.** Each component is labeled with a
model-validity status so users can distinguish validated calculator coverage from approximate or
unsupported categories:

- **Validated** (green) — category-specific calculator with domain-appropriate methodology
- **Approximate** (yellow) — generic mass-based estimate; treat as directional
- **Unsupported** (red) — not modeled; no misleading result is shown

### Provenance & confidence

Every mapped field carries a source type (`pmf_imported` / `pmf_inferred` / `class_default` /
`model_default`) and a confidence level (high / medium / low), plus warnings when values are
snapped or approximated. In public demo mode these refer to demo-safe source categories.

### Versioning & auditability

Every result is stamped with `model_version`, `data_version`, and an `assumptions_hash`. Golden
scenario snapshot tests assert calculator outputs to tolerance, and a formula-trace mode
(`POST /api/calculate?debug=true`) returns step-by-step intermediate values.

---

## Environment variables

### Backend

| Variable | Default | Purpose |
|---------|---------|---------|
| `PUBLIC_DEMO_MODE` | `false` | When `true`, loads only demo-safe/external data and enforces the dataset guardrail. Set to `true` on Vercel. |
| `DATA_MODE` | `external` | `external` (demo-safe) or `internal`. `PUBLIC_DEMO_MODE=true` forces `external`. |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated allow-list. No wildcard. |
| `VERCEL_URL` | (auto) | Injected by Vercel; added to the CORS allow-list automatically. |

### Frontend

| Variable | Default | Purpose |
|---------|---------|---------|
| `VITE_API_BASE_URL` | `/api` (prod), `http://localhost:8000/api` (dev via `.env.development`) | API base URL. Production uses same-origin `/api`. |
| `VITE_PUBLIC_DEMO_MODE` | `true` (prod) | Marks the deployment as a public demo. |

## Public vs. internal data mode

- **Public / external mode** (`PUBLIC_DEMO_MODE=true` or `DATA_MODE=external`): only the bundled,
  demo-safe CSVs under `backend/data/` may be loaded. The `require_public_safe_dataset()`
  guardrail in `backend/app/config.py` rejects any dataset path outside that directory or
  containing internal/confidential/proprietary/private/restricted markers.
- **Internal mode** (`DATA_MODE=internal`, non-public deployments only): the same architecture
  can point at internal data adapters. **No internal data ships in this repository.**

The current data mode is exposed at `GET /api/config` and shown as a badge in the UI.

---

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for full Vercel instructions. In short: the repo ships
`vercel.json`, `api/index.py` (serverless FastAPI entrypoint), and a root `requirements.txt`. The
frontend builds as a static site; `/api/*` routes to the Python serverless function.

Set `PUBLIC_DEMO_MODE=true` in the Vercel project environment.

## API endpoints

Interactive docs at **http://localhost:8000/docs** when the backend is running.

| Endpoint | Purpose |
|---------|---------|
| `GET /api/health` | Health check |
| `GET /api/config` | Data mode + version stamps (drives the demo badge) |
| `POST /api/calculate` | Enclosure calculator (`?debug=true` for formula trace) |
| `POST /api/packaging/calculate` | Packaging calculator |
| `GET /api/packaging/materials` | Packaging materials + GWP values |
| `POST /api/pmf/map-component` | Map a demo component to a scenario with provenance + validity |
| `POST /api/pmf/product-impact` | Product-level rollup of a component change |
| `POST /api/optimize` | Constrained optimization |
| `GET /api/reference/demo-scenarios` | Guided demo scenarios |
| `GET /api/reference/materials`, `/grid-options`, `/blank-types`, `/presets`, `/parameter-contract` | Reference data |
| `GET/POST /api/scenarios`, `POST /api/scenarios/compare` | Scenario persistence & comparison |
| `POST /api/export/csv`, `/export/diff-csv` | CSV export |

> Note: the frontend consumes reference data via the endpoints above rather than a single
> `/api/reference-data` route. Endpoint names are preserved from the existing app.

## Testing

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # if not already created
pip install -r requirements.txt
pytest tests/ -v
```

95 tests cover the calculation engine, golden-scenario snapshots, parameter contract, component
classification, PMF mapping, optimizer, calculator purity, and scenario persistence.

Frontend build / type-check / lint:

```bash
cd frontend
npm install
npm run build     # tsc + vite build
npm run lint
```

## Limitations & disclaimer

**This tool provides scenario estimates for exploratory engineering analysis. It is not a
certified LCA, regulatory carbon accounting report, or official product environmental report.**

Not yet modeled (components in these categories are marked, not silently estimated):

- **PCB / flex circuits** — requires an area-based calculator (CO2e/m²)
- **Textiles / soft goods** — requires a fiber supply-chain model
- **Specialty metals (titanium)** — requires alloy-specific profiles
- **Transportation / logistics** — requires a route-based modal-split model

## License

MIT
