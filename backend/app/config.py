import hashlib
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
ALLOY_CSV = DATA_DIR / "alloy_carbon_intensity.csv"
SUPPORTING_CSV = DATA_DIR / "supporting_data.csv"
FOOTPRINT_DIR = DATA_DIR / "footprint"
PMF_DIR = DATA_DIR / "pmf"
SCENARIOS_FILE = DATA_DIR / "saved_scenarios.json"


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse a boolean-ish environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# --- Data mode / public demo configuration -------------------------------
#
# PUBLIC_DEMO_MODE: when true (the default for the public Vercel deployment),
#   the app loads only demo-safe, external/synthetic datasets and blocks any
#   attempt to reference internal/private/absolute dataset paths.
# DATA_MODE: "external" (demo-safe) or "internal". Public deployments must use
#   "external". PUBLIC_DEMO_MODE forces "external" regardless of this value.
#
# Serverless filesystems are read-only, so PUBLIC_DEMO_MODE also implies that
# scenario persistence stays in-memory only (handled gracefully by the store).
PUBLIC_DEMO_MODE = _env_flag("PUBLIC_DEMO_MODE", default=False)
DATA_MODE = "external" if PUBLIC_DEMO_MODE else os.environ.get("DATA_MODE", "external").strip().lower()

# Bump MODEL_VERSION when calculation formulas change
MODEL_VERSION = "1.0.0"

# Bump DATA_VERSION when CSV data files are updated
DATA_VERSION = "2026-04-17"


class UnsafeDatasetError(Exception):
    """Raised when a dataset path is not safe for a public/external deployment."""


def require_public_safe_dataset(path: "str | Path") -> None:
    """Guardrail: reject internal, private, absolute, or out-of-tree dataset paths.

    Only enforced when running in public demo / external data mode. Ensures the
    public deployment can never be pointed at internal or confidential data by a
    stray environment variable or path. Demo-safe data lives under ``DATA_DIR``.
    """
    if not (PUBLIC_DEMO_MODE or DATA_MODE == "external"):
        return

    p = Path(path)
    resolved = p.resolve()
    data_root = DATA_DIR.resolve()

    # Must live inside the bundled, demo-safe data directory.
    if data_root not in resolved.parents and resolved != data_root:
        raise UnsafeDatasetError(
            f"Refusing to load dataset outside the demo-safe data directory in "
            f"public/external mode: {path}"
        )

    # Reject obvious internal/confidential markers in the path.
    lowered = str(resolved).lower()
    banned = ("internal", "confidential", "proprietary", "private", "restricted")
    hit = next((b for b in banned if b in lowered), None)
    if hit:
        raise UnsafeDatasetError(
            f"Refusing to load dataset with disallowed marker '{hit}' in "
            f"public/external mode: {path}"
        )


def data_mode_info() -> dict:
    """Return the current data-mode configuration for the API/UI."""
    return {
        "public_demo_mode": PUBLIC_DEMO_MODE,
        "data_mode": DATA_MODE,
        "dataset_label": "Public demo dataset — synthetic / external data only",
        "model_version": MODEL_VERSION,
        "data_version": DATA_VERSION,
    }

# Bump MODEL_VERSION when calculation formulas change
MODEL_VERSION = "1.0.0"

# Bump DATA_VERSION when CSV data files are updated
DATA_VERSION = "2026-04-17"


def compute_assumptions_hash(grid_intensities: dict, alloy_materials: list[str],
                             process_param_keys: list[str]) -> str:
    """SHA-256 hash of the key assumptions feeding the model.
    Changes when grid values, materials list, or process params change."""
    payload = json.dumps({
        "grids": sorted(grid_intensities.items()),
        "materials": sorted(alloy_materials),
        "process_keys": sorted(process_param_keys),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
