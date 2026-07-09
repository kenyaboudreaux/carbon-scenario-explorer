from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .engine.data_loader import load_all, validate_loaded_data
from .engine.pmf_loader import load_pmf_data
from .store.scenario_store import ScenarioStore
from .models.products import BASELINE_PRESETS, DEMO_SCENARIOS
from .config import PUBLIC_DEMO_MODE, DATA_MODE, data_mode_info
from .routers import calculate, reference, scenarios, export, optimize, pmf
from .routers import packaging as packaging_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Carbon Scenario Explorer — starting up...")
    logger.info(f"Data mode: {DATA_MODE} (public_demo_mode={PUBLIC_DEMO_MODE})")

    data = load_all()
    validate_loaded_data(data)
    app.state.loaded_data = data

    pmf = load_pmf_data()
    app.state.pmf_data = pmf

    app.state.scenario_store = ScenarioStore()

    total_components = sum(len(p.components) for p in pmf.values())
    logger.info(
        f"Ready: {len(data.alloy_carbon_intensity)} materials, "
        f"{len(data.grid_intensities)} grids, "
        f"{len(pmf)} PMF products ({total_components} components), "
        f"{len(BASELINE_PRESETS)} presets, "
        f"{len(DEMO_SCENARIOS)} demo scenarios"
    )
    yield


app = FastAPI(title="Carbon Scenario Explorer", lifespan=lifespan)

# CORS: explicit allow-list for local dev + optional deployment origins.
# Never a wildcard with credentials. On Vercel the frontend and API are
# same-origin (served under one domain), so CORS is only needed for local dev
# and any extra origins listed via env.
_default_origins = "http://localhost:5173,http://localhost:3000"
_cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]
# Allow the current Vercel deployment URL (auto-injected by Vercel) if present.
_vercel_url = os.environ.get("VERCEL_URL")
if _vercel_url:
    _cors_origins.append(f"https://{_vercel_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(calculate.router)
app.include_router(reference.router)
app.include_router(scenarios.router)
app.include_router(export.router)
app.include_router(optimize.router)
app.include_router(pmf.router)
app.include_router(packaging_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def config():
    """Public runtime config — data mode + version stamps for the UI badge."""
    return data_mode_info()
