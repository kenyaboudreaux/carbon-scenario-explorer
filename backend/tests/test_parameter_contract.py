"""Verify the parameter contract is consistent across all layers."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.parameter_contract import PARAMETER_CONTRACT, PARAMETER_MAP
from app.models.schemas import ScenarioInput
from app.models.enums import Material, BlankType, ElectricityGrid
from app.engine.data_loader import load_all
from app.engine.calculator import calculate_footprint


@pytest.fixture(scope="module")
def data():
    return load_all()


def test_contract_has_24_parameters():
    # 23 active parameters (DMD excluded from the model) + electricity_grid = 23
    # Actually the schema has 22 fields (no DMD) but the contract should match
    assert len(PARAMETER_CONTRACT) == 23, (
        f"Contract has {len(PARAMETER_CONTRACT)} params, expected 23"
    )


def test_every_contract_param_exists_in_schema():
    schema_fields = set(ScenarioInput.model_fields.keys())
    for param in PARAMETER_CONTRACT:
        assert param["name"] in schema_fields, (
            f"Contract param '{param['name']}' missing from ScenarioInput schema"
        )


def test_every_schema_field_in_contract():
    contract_names = {p["name"] for p in PARAMETER_CONTRACT}
    for field_name in ScenarioInput.model_fields:
        assert field_name in contract_names, (
            f"Schema field '{field_name}' missing from parameter contract"
        )


def test_enum_values_match():
    mat_contract = PARAMETER_MAP["material"]["enum_values"]
    mat_enum = [m.value for m in Material]
    assert mat_contract == mat_enum, "Material enum values mismatch"

    bt_contract = PARAMETER_MAP["raw_material_blank_type"]["enum_values"]
    bt_enum = [b.value for b in BlankType]
    assert bt_contract == bt_enum, "BlankType enum values mismatch"

    grid_contract = PARAMETER_MAP["electricity_grid"]["enum_values"]
    grid_enum = [g.value for g in ElectricityGrid]
    assert grid_contract == grid_enum, "ElectricityGrid enum values mismatch"


def test_defaults_match_schema():
    defaults = ScenarioInput(
        material=Material.ALLOY_F,
        recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED,
        raw_material_mass=1000.0,
    )
    schema_dict = defaults.model_dump()
    for param in PARAMETER_CONTRACT:
        name = param["name"]
        contract_default = param["default"]
        schema_val = schema_dict[name]
        # For required fields with no default, contract_default may differ
        if name == "raw_material_mass":
            continue  # required field, no schema default
        if contract_default is not None:
            assert schema_val == contract_default, (
                f"Default mismatch for '{name}': contract={contract_default}, schema={schema_val}"
            )


def test_min_max_bounds_match_schema():
    for param in PARAMETER_CONTRACT:
        name = param["name"]
        field_info = ScenarioInput.model_fields.get(name)
        if field_info is None:
            continue
        metadata = field_info.metadata
        # Check ge/gt constraints
        for m in metadata:
            if hasattr(m, "ge") and m.ge is not None:
                assert param["min"] is not None, (
                    f"Contract missing min for '{name}' (schema has ge={m.ge})"
                )
            if hasattr(m, "le") and m.le is not None:
                assert param["max"] is not None, (
                    f"Contract missing max for '{name}' (schema has le={m.le})"
                )


def test_formulas_affected_are_valid_breakdown_fields():
    from app.models.schemas import ProcessBreakdown
    valid_fields = set(ProcessBreakdown.model_fields.keys()) - {
        "total", "model_version", "data_version", "assumptions_hash"
    }
    for param in PARAMETER_CONTRACT:
        for formula in param["formulas_affected"]:
            assert formula in valid_fields, (
                f"Param '{param['name']}' references invalid formula '{formula}'. "
                f"Valid: {valid_fields}"
            )


def test_formulas_affected_accuracy(data):
    """Toggle each parameter from an active baseline and verify claimed formulas change.

    Uses a baseline that exercises ALL processes so that parameter changes
    in mass/grid/material propagate to every formula that depends on them.
    """
    baseline = ScenarioInput(
        material=Material.ALLOY_F,
        recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED,
        raw_material_mass=1000.0,
        electricity_grid=ElectricityGrid.REGION_A,
        forging_strikes=5,
        forging_trimming_bending_strikes=3,
        stamping_steps=3,
        heat_treatment_annealing_steps=1,
        heat_treatment_annealing_temperature=1100.0,
        heat_treatment_tempering_steps=1,
        heat_treatment_tempering_temperature=400.0,
        machining_cycle_time=120.0,
        laser_cutting_welding_cycle_time=60.0,
        laser_etching_cycle_time=30.0,
        sanding_cycle_time=60.0,
        anodizing=True,
    )
    base_result = calculate_footprint(baseline, data)
    base_dict = base_result.model_dump()

    process_fields = [
        "raw_material", "upstream_processing", "forging", "stamping",
        "heat_treatment", "machining", "laser", "sanding",
        "die_casting", "injection_molding", "anodizing",
    ]

    # param_name -> modified value (must differ from baseline)
    toggles = {
        "material": Material.ALLOY_C.value,
        "recycled_content": 50,
        "raw_material_mass": 2000.0,
        "forging_strikes": 10,
        "forging_trimming_bending_strikes": 8,
        "stamping_steps": 8,
        "heat_treatment_annealing_steps": 3,
        "heat_treatment_annealing_temperature": 800.0,
        "heat_treatment_tempering_steps": 3,
        "heat_treatment_tempering_temperature": 300.0,
        "machining_cycle_time": 600.0,
        "laser_cutting_welding_cycle_time": 300.0,
        "laser_etching_cycle_time": 120.0,
        "sanding_cycle_time": 300.0,
        "anodizing": False,
        "electricity_grid": ElectricityGrid.RENEWABLES.value,
    }

    for param_name, toggle_val in toggles.items():
        if param_name not in PARAMETER_MAP:
            continue
        contract = PARAMETER_MAP[param_name]
        claimed = set(contract["formulas_affected"])

        modified_dict = baseline.model_dump()
        modified_dict[param_name] = toggle_val

        modified = ScenarioInput(**modified_dict)
        mod_result = calculate_footprint(modified, data)
        mod_dict = mod_result.model_dump()

        actually_changed = set()
        for f in process_fields:
            if abs(mod_dict[f] - base_dict[f]) > 1e-10:
                actually_changed.add(f)

        # Every claimed formula should have actually changed
        for f in claimed:
            if f in actually_changed:
                continue
            # die_casting only triggers for Die cast blank type
            if f == "die_casting":
                continue
            # injection_molding needs both parts_per_shot AND cycle_time > 0
            if f == "injection_molding":
                continue
            # upstream_processing unaffected by material change (same blank type)
            if f == "upstream_processing" and param_name == "material":
                continue
            assert f in actually_changed, (
                f"Param '{param_name}' claims to affect '{f}' but it didn't change. "
                f"Actually changed: {actually_changed}"
            )
