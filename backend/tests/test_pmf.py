"""PMF loader, mapper, and component classification regression tests.

Tests use synthetic sample data shipped with the public version.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.pmf_loader import load_pmf_data
from app.engine.pmf_mapper import map_pmf_component, generate_mapping_report, _snap_rc_to_bucket
from app.models.component_classes import (
    ComponentClass, classify_component, CLASS_CONSTRAINTS,
)
from app.models.enums import Material, BlankType


@pytest.fixture(scope="module")
def pmf():
    return load_pmf_data()


class TestPMFLoader:
    def test_products_loaded(self, pmf):
        assert len(pmf) >= 5, f"Expected >= 5 sample products, got {len(pmf)}"

    def test_sample_phone_exists(self, pmf):
        assert "SP200" in pmf, "Smartphone Pro (SP200) should be loaded"
        sp200 = pmf["SP200"]
        assert sp200.name == "Smartphone Pro"
        assert len(sp200.components) >= 8

    def test_sample_laptop_exists(self, pmf):
        lp400 = pmf.get("LP400")
        assert lp400 is not None
        assert lp400.product_group == "Laptop"
        assert len(lp400.components) >= 10

    def test_all_products_positive_mass(self, pmf):
        for prog, p in pmf.items():
            assert p.total_mass_shipped_g > 0, f"{prog} has zero or negative mass"

    def test_recycled_content_in_range(self, pmf):
        for prog, p in pmf.items():
            assert 0 <= p.recycled_content_pct <= 100, (
                f"{prog} RC {p.recycled_content_pct}% out of range"
            )

    def test_housing_component_present(self, pmf):
        housing_count = sum(1 for p in pmf.values() if "Housing" in p.components)
        assert housing_count >= 4, f"Expected >= 4 products with Housing, got {housing_count}"


class TestComponentClasses:
    def test_housing_classifies_metal_structural(self):
        assert classify_component("Housing") == ComponentClass.METAL_STRUCTURAL

    def test_battery_classifies_battery(self):
        assert classify_component("Battery") == ComponentClass.BATTERY

    def test_display_classifies_display(self):
        assert classify_component("Display_assembly") == ComponentClass.DISPLAY

    def test_mlb_classifies_pcb(self):
        assert classify_component("MLB") == ComponentClass.PCB_ELECTRONIC

    def test_speaker_classifies_hardware(self):
        assert classify_component("Speaker") == ComponentClass.HARDWARE_FASTENER

    def test_keyboard_classifies_polymer(self):
        assert classify_component("Keyboard") == ComponentClass.POLYMER_HOUSING

    def test_thermal_mgmt_classifies_thermal(self):
        assert classify_component("Thermal_Mgmt") == ComponentClass.THERMAL

    def test_fallback_aluminum_to_metal(self):
        assert classify_component("UnknownPart", "Aluminum") == ComponentClass.METAL_STRUCTURAL

    def test_fallback_unknown_to_other(self):
        assert classify_component("UnknownPart") == ComponentClass.OTHER

    def test_all_pmf_components_classify(self, pmf):
        for prog, product in pmf.items():
            for comp in product.components.values():
                cls = classify_component(comp.component, comp.dominant_material_category)
                assert cls is not None
                assert isinstance(cls, ComponentClass)

    def test_class_constraints_materials_valid(self):
        valid_materials = {m.value for m in Material}
        for cls, constraints in CLASS_CONSTRAINTS.items():
            for mat in constraints["allowed_materials"]:
                assert mat in valid_materials, f"Class {cls.value} has invalid material: {mat}"

    def test_class_constraints_blank_types_valid(self):
        valid_bts = {b.value for b in BlankType}
        for cls, constraints in CLASS_CONSTRAINTS.items():
            for bt in constraints["allowed_blank_types"]:
                assert bt in valid_bts, f"Class {cls.value} has invalid blank type: {bt}"


class TestPMFMapper:
    def test_rc_snap_basic(self):
        bucket, dist = _snap_rc_to_bucket(32.5, [0, 25, 30, 50, 75, 100])
        assert bucket == 30

    def test_rc_snap_exact(self):
        bucket, dist = _snap_rc_to_bucket(50.0, [0, 25, 30, 50, 75, 100])
        assert bucket == 50
        assert dist == 0.0

    def test_rc_snap_restricted(self):
        bucket, dist = _snap_rc_to_bucket(35.0, [0])
        assert bucket == 0

    def test_housing_mapping(self, pmf):
        sp200 = pmf["SP200"]
        housing = sp200.components["Housing"]
        result = map_pmf_component(sp200, housing)
        assert result.component_class == "metal_structural"
        assert result.provenance["raw_material_mass"]["source"] == "pmf_imported"
        assert result.provenance["raw_material_mass"]["confidence"] == "high"

    def test_provenance_completeness(self, pmf):
        sp200 = pmf["SP200"]
        housing = sp200.components["Housing"]
        result = map_pmf_component(sp200, housing)
        for field in ["raw_material_mass", "material", "recycled_content", "raw_material_blank_type"]:
            assert field in result.provenance
            prov = result.provenance[field]
            assert prov["source"] in ("pmf_imported", "pmf_inferred", "class_default", "model_default")
            assert prov["confidence"] in ("high", "medium", "low")

    def test_confidence_score_in_range(self, pmf):
        for product in pmf.values():
            for comp in product.components.values():
                result = map_pmf_component(product, comp)
                assert 0 <= result.confidence_score <= 1.0


class TestMappingReport:
    def test_report_structure(self, pmf):
        report = generate_mapping_report(pmf)
        assert "generated_at" in report
        assert report["total_products"] >= 5
        assert "mapping_summary" in report
        assert "material_coverage" in report
        assert len(report["products"]) >= 5
