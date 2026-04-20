import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
ALLOY_CSV = DATA_DIR / "alloy_carbon_intensity.csv"
SUPPORTING_CSV = DATA_DIR / "supporting_data.csv"
FOOTPRINT_DIR = DATA_DIR / "footprint"
SCENARIOS_FILE = DATA_DIR / "saved_scenarios.json"

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
