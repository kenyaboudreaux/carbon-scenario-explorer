"""Scenario persistence integrity tests."""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.data_loader import load_all
from app.engine.calculator import calculate_footprint
from app.models.schemas import ScenarioInput, ScenarioCreate, SavedScenario
from app.models.enums import Material, BlankType, ElectricityGrid
from app.store.scenario_store import ScenarioStore


@pytest.fixture(scope="module")
def data():
    return load_all()


@pytest.fixture
def temp_store(tmp_path):
    """ScenarioStore backed by a temp file — completely isolated from runtime."""
    return ScenarioStore(persistence_path=tmp_path / "test_scenarios.json")


def _make_full_input() -> ScenarioInput:
    """Create a ScenarioInput with all 23 parameters explicitly set."""
    return ScenarioInput(
        material=Material.ALLOY_F,
        recycled_content=50,
        raw_material_blank_type=BlankType.EXTRUDED,
        final_part_mass=201.0,
        final_part_volume=75000.0,
        raw_material_mass=1362.7,
        raw_material_volume=500000.0,
        final_part_yield=0.85,
        plastic_injection_molding_parts_per_shot=0,
        plastic_injection_molding_cycle_time=0,
        forging_strikes=5,
        forging_trimming_bending_strikes=3,
        stamping_steps=3,
        heat_treatment_annealing_steps=1,
        heat_treatment_annealing_temperature=1100.0,
        heat_treatment_tempering_steps=1,
        heat_treatment_tempering_temperature=400.0,
        laser_cutting_welding_cycle_time=60.0,
        laser_etching_cycle_time=30.0,
        sanding_cycle_time=60.0,
        machining_cycle_time=120.0,
        anodizing=True,
        electricity_grid=ElectricityGrid.REGION_B,
    )


def test_all_24_params_persisted(temp_store, data):
    """Every input parameter must survive save -> load cycle."""
    inp = _make_full_input()
    req = ScenarioCreate(name="full_params_test", input=inp, notes="Testing persistence")
    saved = temp_store.create(req, data)

    loaded = temp_store.get(saved.id)
    assert loaded is not None

    orig = inp.model_dump()
    stored = loaded.input.model_dump()
    for key in orig:
        assert stored[key] == orig[key], (
            f"Parameter '{key}' mismatch: expected {orig[key]}, got {stored[key]}"
        )


def test_json_reload_integrity(tmp_path, data):
    """Save to JSON, create a NEW store from the same file, verify all fields match."""
    temp_file = tmp_path / "reload_test.json"

    store1 = ScenarioStore(persistence_path=temp_file)
    inp = _make_full_input()
    req = ScenarioCreate(name="reload_test", input=inp)
    saved = store1.create(req, data)
    saved_id = saved.id

    # Create a fresh store from the same file
    store2 = ScenarioStore(persistence_path=temp_file)
    loaded = store2.get(saved_id)
    assert loaded is not None
    assert loaded.name == "reload_test"
    assert loaded.input.model_dump() == inp.model_dump()
    assert loaded.breakdown.total == saved.breakdown.total


def test_version_fields_present(temp_store, data):
    """Saved scenarios must include model_version, data_version, assumptions_hash."""
    inp = ScenarioInput(
        material=Material.ALLOY_F, recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED, raw_material_mass=1000.0,
    )
    req = ScenarioCreate(name="version_test", input=inp)
    saved = temp_store.create(req, data)

    assert saved.model_version != "unknown", "model_version should be set on new scenarios"
    assert saved.data_version != "unknown", "data_version should be set on new scenarios"
    assert saved.assumptions_hash != "unknown", "assumptions_hash should be set on new scenarios"
    assert saved.model_version == saved.breakdown.model_version


def test_timestamps_present(temp_store, data):
    """created_at and updated_at must be set."""
    inp = ScenarioInput(
        material=Material.ALLOY_F, recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED, raw_material_mass=1000.0,
    )
    req = ScenarioCreate(name="timestamp_test", input=inp)
    saved = temp_store.create(req, data)

    assert saved.created_at, "created_at should be set"
    assert saved.updated_at, "updated_at should be set"
    assert "T" in saved.created_at, "created_at should be ISO format"


def test_breakdown_matches_fresh_calculation(temp_store, data):
    """Saved breakdown must match a fresh calculation of the same input."""
    inp = _make_full_input()
    req = ScenarioCreate(name="freshness_test", input=inp)
    saved = temp_store.create(req, data)

    fresh = calculate_footprint(inp, data)
    fields = [
        "raw_material", "upstream_processing", "forging", "stamping",
        "heat_treatment", "machining", "laser", "sanding",
        "die_casting", "injection_molding", "anodizing", "total",
    ]
    for field in fields:
        assert abs(getattr(saved.breakdown, field) - getattr(fresh, field)) < 1e-10, (
            f"Breakdown field '{field}' mismatch: "
            f"saved={getattr(saved.breakdown, field)}, fresh={getattr(fresh, field)}"
        )


def test_runtime_store_not_affected_by_tests(tmp_path, data):
    """Tests must not write to the runtime scenario file."""
    from app.config import SCENARIOS_FILE

    # Record initial state of runtime file
    initial_content = SCENARIOS_FILE.read_text() if SCENARIOS_FILE.exists() else "[]"
    initial_count = len(json.loads(initial_content))

    # Create scenarios in a temp store
    temp_store = ScenarioStore(persistence_path=tmp_path / "isolation_test.json")
    inp = ScenarioInput(
        material=Material.ALLOY_F, recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED, raw_material_mass=1000.0,
    )
    for i in range(5):
        temp_store.create(ScenarioCreate(name=f"isolation_test_{i}", input=inp), data)

    # Verify runtime file was not modified
    after_content = SCENARIOS_FILE.read_text() if SCENARIOS_FILE.exists() else "[]"
    after_count = len(json.loads(after_content))
    assert after_count == initial_count, (
        f"Runtime scenario file was modified by test: {initial_count} -> {after_count}"
    )


def test_temp_store_is_independent(tmp_path, data):
    """Two temp stores with different paths don't interfere."""
    store_a = ScenarioStore(persistence_path=tmp_path / "a.json")
    store_b = ScenarioStore(persistence_path=tmp_path / "b.json")

    inp = ScenarioInput(
        material=Material.ALLOY_F, recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED, raw_material_mass=1000.0,
    )
    store_a.create(ScenarioCreate(name="only_in_a", input=inp), data)

    assert len(store_a.list_all()) == 1
    assert len(store_b.list_all()) == 0
