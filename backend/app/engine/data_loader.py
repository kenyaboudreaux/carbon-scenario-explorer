"""Load CSV data files into in-memory lookup structures at startup."""

from dataclasses import dataclass, field
import logging
import math
import pandas as pd

from ..config import ALLOY_CSV, SUPPORTING_CSV, FOOTPRINT_DIR, compute_assumptions_hash

logger = logging.getLogger(__name__)


@dataclass
class LoadedData:
    # {material_name: {rc_pct_str: kg_CO2e_per_kg}}  e.g. {"Alloy-F": {"0%": 5.32, ...}}
    alloy_carbon_intensity: dict[str, dict[str, float]] = field(default_factory=dict)
    # {material_name: {element: pct}} e.g. {"Alloy-F": {"Cr": 0.0, "Al": 98.74, ...}}
    alloy_compositions: dict[str, dict[str, float]] = field(default_factory=dict)
    # flat dict keyed by Data column from supporting_data.csv
    process_params: dict[str, float] = field(default_factory=dict)
    # {grid_name: kg_CO2e_per_kWh}
    grid_intensities: dict[str, float] = field(default_factory=dict)
    # {blank_type: {extrusion: util, sheet_rolling: util, casting: util}}
    upstream_utilization: dict[str, dict[str, float]] = field(default_factory=dict)
    # {product_code: DataFrame}
    footprint_data: dict[str, pd.DataFrame] = field(default_factory=dict)
    # computed hash of key assumptions
    assumptions_hash: str = ""


def load_all() -> LoadedData:
    data = LoadedData()
    _load_alloy_data(data)
    _load_supporting_data(data)
    _load_upstream_utilization(data)
    _load_footprint_data(data)
    data.assumptions_hash = compute_assumptions_hash(
        data.grid_intensities,
        list(data.alloy_carbon_intensity.keys()),
        list(data.process_params.keys()),
    )
    return data


def _load_alloy_data(data: LoadedData) -> None:
    df = pd.read_csv(ALLOY_CSV, index_col=0)
    materials_list = list(df.columns)

    # Rows 0-12 (index labels Cr..Al) are alloy compositions
    composition_rows = df.iloc[:13]
    for mat in materials_list:
        col = composition_rows[mat]
        comp = {}
        for element, val in col.items():
            try:
                comp[element] = float(val)
            except (ValueError, TypeError):
                comp[element] = None
        data.alloy_compositions[mat] = comp

    # Rows 18-23 (index labels "0%".."100%") are carbon intensity by recycled content
    # Skip rows 13-17 (notes and blanks) — they have index labels like "industry data", ""
    rc_rows = df.iloc[18:]
    for mat in materials_list:
        intensity_map = {}
        for rc_label, val in rc_rows[mat].items():
            rc_label = str(rc_label).strip()
            try:
                fval = float(val)
                if math.isnan(fval):
                    continue  # skip NaN (from "n/a" in CSV)
                intensity_map[rc_label] = fval
            except (ValueError, TypeError):
                pass  # "n/a" entries for TPU
        data.alloy_carbon_intensity[mat] = intensity_map


def _load_supporting_data(data: LoadedData) -> None:
    df = pd.read_csv(SUPPORTING_CSV)
    df = df.dropna(how="all")

    for _, row in df.iterrows():
        key = row.get("Data")
        val = row.get("Value")
        if pd.notna(key) and pd.notna(val):
            try:
                data.process_params[str(key).strip()] = float(val)
            except (ValueError, TypeError):
                pass

    # Extract grid intensities
    data.grid_intensities = {
        "Region A": data.process_params.get("Region A", 0.82),
        "Region B": data.process_params.get("Region B", 0.61),
        "Region C": data.process_params.get("Region C", 0.66),
        "100% renewables": data.process_params.get(
            "100% renewables", 0.07
        ),
    }


def _load_upstream_utilization(data: LoadedData) -> None:
    pp = data.process_params
    ext_util = pp.get("Upstream extrusion utilization", 0.63)
    roll_util = pp.get("Upstream sheet rolling utilization", 0.71)
    cast_util = pp.get("Upstream casting utilization", 0.86)

    data.upstream_utilization = {
        "Extruded": {
            "extrusion": ext_util,
            "sheet_rolling": 1.0,
            "casting": cast_util,
        },
        "Rolled sheet": {
            "extrusion": 1.0,
            "sheet_rolling": roll_util,
            "casting": cast_util,
        },
        "Rolled plate >3mm": {
            "extrusion": 1.0,
            "sheet_rolling": 0.49,
            "casting": 0.85,
        },
        "Injection molded plastic": {
            "extrusion": 1.0,
            "sheet_rolling": 1.0,
            "casting": 1.0,
        },
        "Die cast": {
            "extrusion": 1.0,
            "sheet_rolling": 1.0,
            "casting": cast_util,
        },
    }


def _load_footprint_data(data: LoadedData) -> None:
    if not FOOTPRINT_DIR.exists():
        return
    for csv_file in FOOTPRINT_DIR.glob("*.csv"):
        name = csv_file.stem
        # e.g. "B9_footprint_ghg_2026_04_17" -> key "B9_ghg"
        parts = name.split("_footprint_")
        if len(parts) == 2:
            product_code = parts[0]
            kind = parts[1].split("_")[0]  # "ghg" or "materials"
            key = f"{product_code}_{kind}"
        else:
            key = name
        data.footprint_data[key] = pd.read_csv(csv_file)


# --- Data Integrity Validation ---

REQUIRED_PROCESS_PARAMS = [
    "Region A", "Region B", "Region C", "100% renewables",
    "Forging strikes", "Trimming/bending strikes", "Stamping presses",
    "Aluminum specific heat", "Heating efficiency", "Starting temperature",
    "Electricity",
    "Upstream sheet rolling utilization",
    "Thermal intensity",
    "Upstream extrusion utilization",
    "Upstream casting utilization",
]

EXPECTED_BLANK_TYPES = [
    "Extruded", "Rolled sheet", "Rolled plate >3mm",
    "Injection molded plastic", "Die cast",
]

ALUMINUM_ALLOYS = [
    "Alloy-A", "Alloy-B", "Alloy-C", "Alloy-D", "Alloy-E",
    "Alloy-F", "Alloy-G", "Alloy-H", "Cast-A", "Cast-B",
]

EXPECTED_RC_LEVELS = {"0%", "25%", "30%", "50%", "75%", "100%"}


class DataIntegrityError(Exception):
    """Raised when data fails critical validation checks."""


def validate_loaded_data(data: LoadedData) -> list[str]:
    """Validate loaded data at startup. Returns list of warnings.
    Raises DataIntegrityError on critical failures."""
    warnings = []
    errors = []

    # --- Materials count ---
    mat_count = len(data.alloy_carbon_intensity)
    if mat_count != 13:
        errors.append(f"CRITICAL: Expected 13 materials, found {mat_count}")
    else:
        logger.info(f"Materials: {mat_count} loaded (OK)")

    # --- Recycled content levels per material ---
    for alloy in ALUMINUM_ALLOYS:
        if alloy not in data.alloy_carbon_intensity:
            errors.append(f"CRITICAL: Missing material '{alloy}' in alloy table")
            continue
        rc_keys = set(data.alloy_carbon_intensity[alloy].keys())
        if rc_keys != EXPECTED_RC_LEVELS:
            missing = EXPECTED_RC_LEVELS - rc_keys
            extra = rc_keys - EXPECTED_RC_LEVELS
            msg = f"Material '{alloy}': RC levels mismatch."
            if missing:
                msg += f" Missing: {missing}."
            if extra:
                msg += f" Extra: {extra}."
            warnings.append(msg)

    # Polymer-A should have specific RC levels
    pa_rcs = set(data.alloy_carbon_intensity.get("Polymer-A", {}).keys())
    expected_pa = {"0%", "25%", "30%", "50%", "75%", "100%"}
    if not pa_rcs:
        errors.append("CRITICAL: No RC data for Polymer-A")
    elif pa_rcs != expected_pa:
        warnings.append(f"Polymer-A RC levels: expected {expected_pa}, got {pa_rcs}")

    # Polymer-B/C should have only 0%
    for poly_name in ["Polymer-B", "Polymer-C"]:
        poly_rcs = set(data.alloy_carbon_intensity.get(poly_name, {}).keys())
        if poly_rcs != {"0%"}:
            if not poly_rcs:
                errors.append(f"CRITICAL: No RC data for {poly_name}")
            else:
                warnings.append(f"{poly_name} RC levels: expected {{'0%'}}, got {poly_rcs}")

    # --- Grid intensities ---
    grid_count = len(data.grid_intensities)
    if grid_count != 4:
        errors.append(f"CRITICAL: Expected 4 grid intensities, found {grid_count}")
    else:
        logger.info(f"Grid intensities: {grid_count} loaded (OK)")

    for grid_name, grid_val in data.grid_intensities.items():
        if math.isnan(grid_val):
            errors.append(f"CRITICAL: NaN grid intensity for '{grid_name}'")
        elif not (0.01 <= grid_val <= 2.0):
            warnings.append(
                f"Grid '{grid_name}' intensity {grid_val} outside expected range [0.01, 2.0]"
            )

    # --- Carbon intensity value ranges ---
    for mat, rc_map in data.alloy_carbon_intensity.items():
        for rc_label, ci_val in rc_map.items():
            if math.isnan(ci_val):
                errors.append(f"CRITICAL: NaN carbon intensity for {mat} @ {rc_label}")
            elif not (0 < ci_val < 50):
                warnings.append(
                    f"Carbon intensity {mat} @ {rc_label} = {ci_val} outside [0, 50] range"
                )

    # --- Required process params ---
    for key in REQUIRED_PROCESS_PARAMS:
        if key not in data.process_params:
            errors.append(f"CRITICAL: Missing process param key '{key}'")
        else:
            val = data.process_params[key]
            if math.isnan(val):
                errors.append(f"CRITICAL: NaN value for process param '{key}'")

    # --- Upstream utilization ---
    if len(data.upstream_utilization) != 5:
        errors.append(
            f"CRITICAL: Expected 5 blank types in upstream_utilization, "
            f"found {len(data.upstream_utilization)}"
        )

    for bt in EXPECTED_BLANK_TYPES:
        if bt not in data.upstream_utilization:
            errors.append(f"CRITICAL: Missing blank type '{bt}' in upstream_utilization")
            continue
        util = data.upstream_utilization[bt]
        for factor_name in ["extrusion", "sheet_rolling", "casting"]:
            if factor_name not in util:
                errors.append(
                    f"CRITICAL: Missing factor '{factor_name}' for blank type '{bt}'"
                )
            else:
                fval = util[factor_name]
                if not (0 < fval <= 1.0):
                    warnings.append(
                        f"Utilization {bt}/{factor_name} = {fval} outside (0, 1]"
                    )

    # --- Log results ---
    for w in warnings:
        logger.warning(f"Data validation: {w}")
    for e in errors:
        logger.error(f"Data validation: {e}")

    if errors:
        raise DataIntegrityError(
            f"Data validation failed with {len(errors)} critical error(s):\n"
            + "\n".join(errors)
        )

    logger.info(
        f"Data validation passed: {mat_count} materials, "
        f"{grid_count} grids, {len(data.upstream_utilization)} blank types, "
        f"{len(warnings)} warning(s)"
    )
    return warnings
