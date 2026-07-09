# Deployment

Carbon Scenario Explorer is **local-first** and also deploys as a public demo on **Vercel**.

## Local

```bash
./start.sh
```

Backend on `localhost:8000`, frontend on `localhost:5173`. See [README.md](README.md) for manual
startup.

---

## Vercel (public demo)

The repository ships everything needed for a monorepo Vercel deployment:

```
api/index.py        # serverless entrypoint — imports the FastAPI app from backend/
requirements.txt    # Python deps for @vercel/python (repo root)
vercel.json         # builds + routes (static frontend + Python API)
frontend/           # Vite static build (distDir: dist)
backend/            # FastAPI app + demo-safe data
```

### How it fits together

`vercel.json` declares two builds:

1. **`api/index.py`** via `@vercel/python` — serves the FastAPI app. `api/index.py` adds
   `backend/` to `sys.path` and imports `app.main:app`. Requests to `/api/*` route here.
2. **`frontend/package.json`** via `@vercel/static-build` — runs `npm run build` and serves
   `frontend/dist`. All non-API routes fall through to `index.html` (SPA routing).

Pandas + FastAPI fit within the `@vercel/python` serverless bundle. Data is loaded from small
bundled CSVs at cold start; scenario persistence falls back to in-memory automatically on the
read-only serverless filesystem (`ScenarioStore` handles `OSError` on write).

### Step-by-step

1. **Push** the repository to GitHub.
2. In Vercel, **Import Project** from the GitHub repo.
3. **Root directory:** leave as the repository root (`vercel.json` handles the monorepo layout).
   Do not set the root to `frontend/`.
4. **Framework preset:** Other (the `vercel.json` `builds` array drives everything). No override of
   build command / output directory is needed.
5. **Environment variables** (Project → Settings → Environment Variables):

   | Variable | Value | Scope |
   |---------|-------|-------|
   | `PUBLIC_DEMO_MODE` | `true` | Production (+ Preview) |
   | `DATA_MODE` | `external` | Production (+ Preview) |
   | `VITE_PUBLIC_DEMO_MODE` | `true` | Production (+ Preview) |

   `VITE_API_BASE_URL` is not required — the frontend defaults to same-origin `/api` in production
   (`frontend/.env.production`). `CORS_ORIGINS` is not required for same-origin serving; `VERCEL_URL`
   is auto-injected and added to the allow-list.

6. **Deploy.**

### Post-deploy verification

1. `GET https://<deployment>/api/health` → `{"status":"ok"}`.
2. `GET https://<deployment>/api/config` → `public_demo_mode: true`, `data_mode: "external"`.
3. Open the site — the header shows a **"Public demo · external data"** badge.
4. Landing page renders hero, "what you can change / get back", model-validity, and demo-safety
   sections.
5. Guided scenarios load and open the modeling view; adjusting parameters recomputes results.
6. Confirm no internal/proprietary strings appear (see [DATA_SAFETY.md](DATA_SAFETY.md)).

### Troubleshooting

- **API 500 at cold start:** check the function logs. Most likely a missing dependency — confirm
  root `requirements.txt` installed.
- **Blank page / 404 on refresh of a sub-route:** ensure the SPA fallback route in `vercel.json`
  (`/(.*) → frontend/dist/index.html`) is present.
- **CORS errors in local dev:** the API allows `http://localhost:5173` by default; override with
  `CORS_ORIGINS` if you run the frontend on a different port.

### Fallback if serverless Python is unsuitable

If a future dependency makes the Python function too heavy for serverless, the frontend can be
deployed static-only and pointed at a separately hosted backend by setting `VITE_API_BASE_URL` to
that backend's URL and adding the frontend origin to the backend's `CORS_ORIGINS`. The full
FastAPI backend always runs locally via `./start.sh`.
