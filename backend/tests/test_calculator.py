"""Unit tests for the carbon footprint calculation engine."""

import sys
from pathlib import Path
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.data_loader import load_all
from app.engine.calculator import calculate_footprint
from app.models.schemas import ScenarioInput
from app.models.enums import Material, BlankType, ElectricityGrid


@pytest.fixture(scope="module")
def data():
    return load_all()


def _make_input(**overrides) -> ScenarioInput:
    defaults = dict(
        material=Material.ALLOY_F,
        recycled_content=100,
        raw_material_blank_type=BlankType.EXTRUDED,
        raw_material_mass=1362.7,
        electricity_grid=ElectricityGrid.REGION_A,
    )
    defaults.update(overrides)
    return ScenarioInput(**defaults)


class TestRawMaterial:
    def test_6r01_100rc(self, data):
        inp = _make_input()
        result = calculate_footprint(inp, data)
        # 1.3627 kg * 0.44 kg CO2e/kg = 0.599588
        assert abs(result.raw_material - 0.599588) < 0.001

    def test_6r01_0rc(self, data):
        inp = _make_input(recycled_content=0)
        result = calculate_footprint(inp, data)
        # 1.3627 * 5.32 = 7.249564
        assert abs(result.raw_material - 7.249564) < 0.01

    def test_pc_0rc(self, data):
        inp = _make_input(
            material=Material.POLYMER_A, recycled_content=0,
            raw_material_blank_type=BlankType.INJECTION_MOLDED,
            raw_material_mass=500.0,
        )
        result = calculate_footprint(inp, data)
        # 0.5 kg * 5.16 = 2.58
        assert abs(result.raw_material - 2.60) < 0.05


class TestForging:
    def test_notebook_oracle(self, data):
        """From the notebook: 5 forging strikes, China grid -> 0.041"""
        inp = _make_input(forging_strikes=5)
        result = calculate_footprint(inp, data)
        assert abs(result.forging - 0.041) < 0.001

    def test_zero_strikes(self, data):
        inp = _make_input(forging_strikes=0)
        result = calculate_footprint(inp, data)
        assert result.forging == 0.0

    def test_with_bending(self, data):
        inp = _make_input(forging_strikes=5, forging_trimming_bending_strikes=10)
        result = calculate_footprint(inp, data)
        # (5*0.01 + 10*0.005) * 0.82 = (0.05 + 0.05) * 0.82 = 0.082
        assert abs(result.forging - 0.082) < 0.001


class TestStamping:
    def test_notebook_oracle(self, data):
        """From the notebook: 3 stamping steps, 1362.7g, China -> 0.01676121"""
        inp = _make_input(stamping_steps=3)
        result = calculate_footprint(inp, data)
        assert abs(result.stamping - 0.01676121) < 0.0001

    def test_zero_steps(self, data):
        inp = _make_input(stamping_steps=0)
        result = calculate_footprint(inp, data)
        assert result.stamping == 0.0


class TestHeatTreatment:
    def test_zero_when_no_steps(self, data):
        inp = _make_input()
        result = calculate_footprint(inp, data)
        assert result.heat_treatment == 0.0

    def test_annealing(self, data):
        inp = _make_input(
            heat_treatment_annealing_steps=1,
            heat_treatment_annealing_temperature=1100.0,
        )
        result = calculate_footprint(inp, data)
        # mass_kg=1.3627, specific_heat=900, delta_T=1075, eff=0.2
        # energy = 1.3627 * 900 * 1075 / (0.2 * 3600000) = 1318452.75 / 720000 = 1.83118
        # * 1 step * 0.82 grid = 1.50157
        assert result.heat_treatment > 1.0
        assert abs(result.heat_treatment - 1.50157) < 0.01


class TestUpstream:
    def test_extruded(self, data):
        inp = _make_input(raw_material_blank_type=BlankType.EXTRUDED)
        result = calculate_footprint(inp, data)
        # (1.3627 / 0.63) * 1.06 * 0.82 = 2.163 * 1.06 * 0.82 = 1.8809
        assert result.upstream_processing > 1.0

    def test_injection_molded_zero(self, data):
        inp = _make_input(
            material=Material.POLYMER_A, recycled_content=0,
            raw_material_blank_type=BlankType.INJECTION_MOLDED,
            raw_material_mass=500.0,
        )
        result = calculate_footprint(inp, data)
        assert result.upstream_processing == 0.0

    def test_die_cast_zero_upstream(self, data):
        inp = _make_input(raw_material_blank_type=BlankType.DIE_CAST)
        result = calculate_footprint(inp, data)
        assert result.upstream_processing == 0.0


class TestMachining:
    def test_machining(self, data):
        inp = _make_input(machining_cycle_time=3600)
        result = calculate_footprint(inp, data)
        # (3600/3600) * 2 * 0.82 = 1.64
        assert abs(result.machining - 1.64) < 0.001

    def test_zero(self, data):
        inp = _make_input(machining_cycle_time=0)
        result = calculate_footprint(inp, data)
        assert result.machining == 0.0


class TestAnodizing:
    def test_enabled(self, data):
        inp = _make_input(anodizing=True)
        result = calculate_footprint(inp, data)
        # 0.2 * 0.82 = 0.164
        assert abs(result.anodizing - 0.164) < 0.001

    def test_disabled(self, data):
        inp = _make_input(anodizing=False)
        result = calculate_footprint(inp, data)
        assert result.anodizing == 0.0


class TestGridSensitivity:
    def test_renewables_much_lower(self, data):
        inp_china = _make_input(forging_strikes=5)
        inp_renew = _make_input(
            forging_strikes=5, electricity_grid=ElectricityGrid.RENEWABLES
        )
        r_china = calculate_footprint(inp_china, data)
        r_renew = calculate_footprint(inp_renew, data)
        # Grid-dependent processes should be ~11.7x lower with renewables
        ratio = r_china.forging / r_renew.forging
        assert abs(ratio - (0.82 / 0.07)) < 0.5


class TestTotal:
    def test_all_zero_processes(self, data):
        inp = _make_input()
        result = calculate_footprint(inp, data)
        # Only raw_material + upstream should be > 0
        assert result.total > 0
        assert result.forging == 0.0
        assert result.stamping == 0.0
        assert result.heat_treatment == 0.0
        assert result.machining == 0.0
        assert result.laser == 0.0
        assert result.sanding == 0.0
        assert result.injection_molding == 0.0
        assert result.total == result.raw_material + result.upstream_processing

    def test_total_is_sum(self, data):
        inp = _make_input(
            forging_strikes=5,
            stamping_steps=3,
            machining_cycle_time=120,
            anodizing=True,
        )
        result = calculate_footprint(inp, data)
        expected_total = (
            result.raw_material + result.upstream_processing +
            result.forging + result.stamping + result.heat_treatment +
            result.machining + result.laser + result.sanding +
            result.die_casting + result.injection_molding + result.anodizing
        )
        assert abs(result.total - expected_total) < 0.0001


class TestValidation:
    def test_tpu_only_0rc(self):
        with pytest.raises(Exception):
            ScenarioInput(
                material=Material.POLYMER_B,
                recycled_content=25,
                raw_material_blank_type=BlankType.INJECTION_MOLDED,
                raw_material_mass=100.0,
            )

    def test_pc_invalid_rc(self):
        with pytest.raises(Exception):
            ScenarioInput(
                material=Material.POLYMER_A,
                recycled_content=25,
                raw_material_blank_type=BlankType.INJECTION_MOLDED,
                raw_material_mass=100.0,
            )
