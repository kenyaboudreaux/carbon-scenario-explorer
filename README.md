# Carbon Scenario Explorer

A category-routed carbon scenario modeling tool with interactive what-if analysis. Select product components, adjust manufacturing or packaging parameters, and see how changes affect carbon footprint outcomes in real time.

The system uses a **multi-calculator architecture** where different product categories are routed to domain-specific calculation engines rather than a single generic model.

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI / Pandas
- **Frontend**: React 19 / TypeScript / Vite / Recharts
- **Data**: CSV-based (PMF format for product data, lookup tables for materials and process constants)
- **Deployment**: Local-first

## Quickstart

```bash
./start.sh
```

Then open **http://localhost:5173**.

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

### Prerequisites
- Python 3.12+
- Node.js 22+

## Architecture

### Category-Routed Calculation Engine

The core design principle is **one engine per product category**, not one universal calculator. Each category has its own input schema, formulas, material database, and output breakdown:

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
    Charts / Comparison / Reports
```

### Validated Calculators

| Calculator | Category | Unit Basis | What It Models |
|-----------|----------|-----------|----------------|
| **Enclosure** | Metal structural, polymer housing, hardware | kg (mass) | 11 manufacturing processes: raw material CI, upstream semi-fabrication, forging, stamping, heat treatment, machining, laser, sanding, die casting, injection molding, anodizing |
| **Packaging** | Packaging components | g (mass) | Material GWP lookup (13 packaging materials) + shipping carbon by modal split (air 7.84 / sea 0.15 / ground 0.45 kg CO2e/kg) |

### Model Validity System

Every component displays a validity badge:

- **Validated** (green) — uses a category-specific calculator with domain-appropriate methodology
- **Approximate** (yellow) — uses the generic enclosure calculator as a mass-based estimate
- **Unsupported** (red) — no applicable calculator; results not available or clearly marked as placeholder

This prevents the system from silently producing inaccurate results for categories it doesn't properly model.

### Project Structure

```
carbon-scenario-explorer/
  api/
    index.py                Serverless entrypoint (imports backend FastAPI app)
  backend/
    app/
      engine/
        calculators/        Category-routed calculation dispatch
          enclosure.py      Mass-based manufacturing (11 formulas)
          packaging.py      Material GWP + shipping modal split
        calculator.py       Core enclosure formula implementation
        data_loader.py      CSV data loading + startup validation
        pmf_loader.py       Product Material Footprint parser
        pmf_mapper.py       PMF → ScenarioInput with provenance
        optimizer.py        Constrained heuristic optimizer
      models/
        schemas.py          Pydantic models (ScenarioInput, ProcessBreakdown, etc.)
        enums.py            Material, BlankType, ElectricityGrid enums
        products.py         Baseline presets and demo scenarios
        component_classes.py  Classification + model validity mapping
      routers/              FastAPI endpoints (calculate, scenarios, pmf, packaging, etc.)
      store/                JSON-based scenario persistence
    data/                   CSV data files, PMF samples, material lookup tables
    tests/                  95 tests + 13 golden scenario snapshots
  frontend/
    src/
      components/           Layout, Controls, Charts, Scenarios, Optimize, Landing, Report, Info
      hooks/                useCalculation, useReferenceData, useScenarios, usePresets
      api/                  Typed API client
      types/                TypeScript interfaces
  start.sh                  One-command launcher with health check
```

## Features

- **Multi-Calculator Architecture** — category-routed calculations (enclosure + packaging, extensible)
- **Model Validity System** — green/yellow/red badges showing calculator coverage per component
- **Product-Backed Data** — 5 sample products with component-level mass and recycled content
- **Product-Level Rollup** — component delta and estimated product-wide impact
- **Interactive Modeling** — 24 configurable parameters with real-time visualization
- **Field Provenance** — every field shows its data source and confidence level
- **Optimization (Beta)** — constrained heuristic for validated categories
- **Scenario Comparison** — side-by-side table and stacked bar chart
- **Scenario Report** — print-ready report with methodology, provenance, and validity

## Current Scope

### What is modeled accurately

- **Metal enclosures / structural parts**: aluminum alloys, die-cast parts, injection-molded polymers — 11 manufacturing process formulas
- **Packaging**: material carbon (13 materials including paper, film, polymer parts) + shipping carbon by air/sea/ground modal split

### What is not yet modeled

- **PCB / flex circuits** — requires area-based calculator (CO2e/m²)
- **Textiles / soft goods** — requires fiber supply-chain model
- **Specialty metals (titanium)** — requires alloy-specific profiles
- **Transportation / logistics** — requires route-based modal split model

Components in unsupported categories display clear validity indicators and do not produce misleading results.

## Bringing Your Own Data

Place CSV files in `backend/data/pmf/` following the schema in `backend/data/README.md`. The app ships with anonymized synthetic sample data.

## API Documentation

Start the backend and visit **http://localhost:8000/docs** for interactive API documentation.

Key endpoints:
- `POST /api/calculate` — enclosure calculator (add `?debug=true` for formula trace)
- `POST /api/packaging/calculate` — packaging calculator
- `GET /api/packaging/materials` — list packaging materials with GWP values
- `POST /api/pmf/map-component` — map PMF component with provenance + validity
- `POST /api/optimize` — constrained optimization

## Running Tests

```bash
cd backend && source venv/bin/activate && pytest tests/ -v
```

95 tests covering: calculation engine, golden scenarios, parameter contract, component classification, PMF mapping, optimizer, and scenario persistence.

## Deployment

### Local
Use `./start.sh` or manual startup. Defaults to `localhost:8000` (backend) and `localhost:5173` (frontend).

## License

MIT
