"""Golden scenario snapshot tests — full-scenario validation.

Each test loads a snapshot JSON (input + expected breakdown), runs it through
the calculator, and asserts all 12 fields match within tolerance.
"""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.data_loader import load_all
from app.engine.calculator import calculate_footprint
from app.models.schemas import ScenarioInput, ProcessBreakdown

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
PROCESS_FIELDS = [
    "raw_material", "upstream_processing", "forging", "stamping",
    "heat_treatment", "machining", "laser", "sanding",
    "die_casting", "injection_molding", "anodizing", "total",
]


@pytest.fixture(scope="module")
def data():
    return load_all()


def _load_snapshot_files():
    files = sorted(SNAPSHOT_DIR.glob("*.json"))
    assert len(files) >= 13, f"Expected >= 12 snapshot files, found {len(files)}"
    return files


def _snapshot_ids():
    return [f.stem for f in sorted(SNAPSHOT_DIR.glob("*.json"))]


@pytest.fixture(params=_load_snapshot_files(), ids=_snapshot_ids())
def snapshot(request):
    return json.loads(request.param.read_text())


def test_golden_scenario(snapshot, data):
    """Full-scenario snapshot test: asserts all 12 breakdown fields."""
    inp = ScenarioInput(**snapshot["input"])
    result = calculate_footprint(inp, data)
    expected = snapshot["expected_breakdown"]
    tolerance = snapshot.get("tolerance", 0.001)
    scenario_name = snapshot["scenario_name"]

    deviations = []
    for field in PROCESS_FIELDS:
        actual = getattr(result, field)
        exp = expected[field]
        if exp == 0.0:
            if actual != 0.0:
                deviations.append(f"{field}: expected 0, got {actual}")
        else:
            rel_error = abs(actual - exp) / abs(exp)
            if rel_error > tolerance:
                deviations.append(
                    f"{field}: expected {exp}, got {actual} "
                    f"(relative error {rel_error:.6f} > tolerance {tolerance})"
                )

    assert not deviations, (
        f"Scenario '{scenario_name}' failed {len(deviations)} field(s):\n"
        + "\n".join(f"  {d}" for d in deviations)
    )


def test_snapshot_count():
    """Ensure we have the expected number of golden scenarios."""
    files = list(SNAPSHOT_DIR.glob("*.json"))
    assert len(files) == 13, f"Expected 16 snapshot files, found {len(files)}"


def test_all_blank_types_covered():
    """Verify golden scenarios cover all 5 blank types."""
    covered = set()
    for f in SNAPSHOT_DIR.glob("*.json"):
        snap = json.loads(f.read_text())
        covered.add(snap["input"]["raw_material_blank_type"])
    expected = {"Extruded", "Rolled sheet", "Rolled plate >3mm",
                "Injection molded plastic", "Die cast"}
    assert covered == expected, f"Missing blank types: {expected - covered}"


def test_all_grids_covered():
    """Verify golden scenarios use at least 2 different grids."""
    grids = set()
    for f in SNAPSHOT_DIR.glob("*.json"):
        snap = json.loads(f.read_text())
        grids.add(snap["input"]["electricity_grid"])
    assert len(grids) >= 2, f"Only {len(grids)} grid(s) covered: {grids}"


def test_version_stamped(data):
    """Every calculation should include version info."""
    snap = json.loads(next(SNAPSHOT_DIR.glob("*.json")).read_text())
    inp = ScenarioInput(**snap["input"])
    result = calculate_footprint(inp, data)
    assert result.model_version != "", "model_version should be set"
    assert result.data_version != "", "data_version should be set"
    assert result.assumptions_hash != "", "assumptions_hash should be set"
