"""Tests for product presets and optimizer."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.products import BASELINE_PRESETS, PRESET_MAP, ProductFamily, ComponentType, FAMILY_COMPONENTS
from app.models.schemas import ScenarioInput
from app.models.enums import Material, BlankType
from app.engine.data_loader import load_all
from app.engine.calculator import calculate_footprint
from app.engine.optimizer import optimize_scenario


@pytest.fixture(scope="module")
def data():
    return load_all()


class TestPresets:
    def test_preset_count(self):
        assert len(BASELINE_PRESETS) == 5

    def test_all_presets_have_required_fields(self):
        required = {"id", "product_family", "component_type", "display_name",
                     "description", "parameters", "adjustable_params",
                     "locked_params", "allowed_materials", "allowed_blank_types"}
        for p in BASELINE_PRESETS:
            missing = required - set(p.keys())
            assert not missing, f"Preset '{p['id']}' missing fields: {missing}"

    def test_all_preset_parameters_are_valid_scenario_inputs(self, data):
        for p in BASELINE_PRESETS:
            inp = ScenarioInput(**p["parameters"])
            result = calculate_footprint(inp, data)
            assert result.total > 0, f"Preset '{p['id']}' produces zero total"

    def test_preset_materials_are_valid(self):
        valid_materials = {m.value for m in Material}
        for p in BASELINE_PRESETS:
            for mat in p["allowed_materials"]:
                assert mat in valid_materials, (
                    f"Preset '{p['id']}' has invalid allowed material: {mat}"
                )

    def test_preset_blank_types_are_valid(self):
        valid_bts = {b.value for b in BlankType}
        for p in BASELINE_PRESETS:
            for bt in p["allowed_blank_types"]:
                assert bt in valid_bts, (
                    f"Preset '{p['id']}' has invalid allowed blank type: {bt}"
                )

    def test_locked_and_adjustable_dont_overlap(self):
        for p in BASELINE_PRESETS:
            overlap = set(p["locked_params"]) & set(p["adjustable_params"])
            assert not overlap, (
                f"Preset '{p['id']}' has params both locked and adjustable: {overlap}"
            )

    def test_preset_map_matches_list(self):
        assert len(PRESET_MAP) == len(BASELINE_PRESETS)
        for p in BASELINE_PRESETS:
            assert p["id"] in PRESET_MAP

    def test_family_components_covers_all_families(self):
        for f in ProductFamily:
            assert f.value in FAMILY_COMPONENTS, f"Missing family: {f.value}"


class TestOptimizer:
    def test_optimizer_reduces_footprint(self, data):
        """Optimizer should always find improvements for a virgin-China baseline."""
        inp = ScenarioInput(
            material=Material.ALLOY_F, recycled_content=0,
            raw_material_blank_type=BlankType.EXTRUDED,
            raw_material_mass=1000.0,
            electricity_grid="Region A",
        )
        result = optimize_scenario(inp, None, data)
        assert result.total_reduction_kg > 0, "Optimizer should reduce footprint"
        assert result.total_reduction_pct > 0
        assert len(result.parameter_diffs) > 0

    def test_optimizer_with_preset(self, data):
        """Test optimization with phone midframe preset."""
        preset = PRESET_MAP["phone_midframe"]
        inp = ScenarioInput(**preset["parameters"])
        result = optimize_scenario(inp, "iphone_midframe", data)
        assert result.total_reduction_kg > 0
        # Should only change adjustable params
        adjustable = set(preset["adjustable_params"])
        for diff in result.parameter_diffs:
            assert diff.parameter in adjustable, (
                f"Optimizer changed locked param: {diff.parameter}"
            )

    def test_optimizer_respects_locked_params(self, data):
        """Locked params should never appear in diffs."""
        for preset_id, preset in PRESET_MAP.items():
            inp = ScenarioInput(**preset["parameters"])
            result = optimize_scenario(inp, preset_id, data)
            locked = set(preset["locked_params"])
            for diff in result.parameter_diffs:
                assert diff.parameter not in locked, (
                    f"Preset '{preset_id}': optimizer changed locked param '{diff.parameter}'"
                )

    def test_optimizer_already_optimal(self, data):
        """If already at 100% RC + renewables, reduction should be minimal or zero."""
        inp = ScenarioInput(
            material=Material.ALLOY_F, recycled_content=100,
            raw_material_blank_type=BlankType.EXTRUDED,
            raw_material_mass=1000.0,
            electricity_grid="100% renewables",
        )
        result = optimize_scenario(inp, None, data)
        # May still find small improvements via material sub, but total should be small
        assert result.total_reduction_pct < 50, "Already near-optimal should not halve"

    def test_optimizer_output_is_valid(self, data):
        """Optimized input should produce a valid calculation."""
        inp = ScenarioInput(
            material=Material.ALLOY_H, recycled_content=0,
            raw_material_blank_type=BlankType.EXTRUDED,
            raw_material_mass=1500.0,
            forging_strikes=10,
            electricity_grid="Region A",
        )
        result = optimize_scenario(inp, None, data)
        # Verify optimized input can be calculated
        check = calculate_footprint(result.optimized_input, data)
        assert abs(check.total - result.optimized_breakdown.total) < 1e-6

    def test_optimizer_all_presets(self, data):
        """Run optimizer on all presets — none should error."""
        for preset_id, preset in PRESET_MAP.items():
            inp = ScenarioInput(**preset["parameters"])
            result = optimize_scenario(inp, preset_id, data)
            assert result.optimized_breakdown.total <= result.baseline_breakdown.total + 0.001, (
                f"Preset '{preset_id}': optimizer made footprint worse"
            )
