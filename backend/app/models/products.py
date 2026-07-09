"""Product families, component types, baseline presets, and optimization rules.

All product names, codes, and parameters in this file are synthetic/sample data
for demonstration purposes only.
"""

from enum import Enum


class ProductFamily(str, Enum):
    PHONE = "Phone"
    TABLET = "Tablet"
    LAPTOP = "Laptop"
    WEARABLE = "Wearable"
    ACCESSORIES = "Accessories"


class ComponentType(str, Enum):
    ENCLOSURE = "Enclosure / Structural"
    MIDFRAME = "Midframe / Chassis"
    BRACKET = "Bracket / Mount"
    CASE = "Case / Housing"
    BAND_METAL = "Band (Metal)"
    BAND_POLYMER = "Band (Polymer/Soft Goods)"
    HINGE = "Hinge / Clasp"
    SPEAKER_GRILLE = "Speaker Grille"
    OTHER = "Other"


FAMILY_COMPONENTS: dict[str, list[str]] = {
    ProductFamily.PHONE: [
        ComponentType.ENCLOSURE, ComponentType.MIDFRAME,
        ComponentType.BRACKET, ComponentType.SPEAKER_GRILLE, ComponentType.OTHER,
    ],
    ProductFamily.TABLET: [
        ComponentType.ENCLOSURE, ComponentType.BRACKET, ComponentType.OTHER,
    ],
    ProductFamily.LAPTOP: [
        ComponentType.ENCLOSURE, ComponentType.BRACKET,
        ComponentType.HINGE, ComponentType.OTHER,
    ],
    ProductFamily.WEARABLE: [
        ComponentType.CASE, ComponentType.BAND_METAL,
        ComponentType.BAND_POLYMER, ComponentType.HINGE, ComponentType.OTHER,
    ],
    ProductFamily.ACCESSORIES: [
        ComponentType.CASE, ComponentType.BRACKET, ComponentType.OTHER,
    ],
}


BASELINE_PRESETS: list[dict] = [
    {
        "id": "phone_midframe",
        "product_family": "Phone",
        "component_type": "Midframe / Chassis",
        "display_name": "Smartphone Midframe (Aluminum)",
        "description": "Extruded aluminum midframe with forging, stamping, machining, and anodizing",
        "parameters": {
            "material": "Alloy-F",
            "recycled_content": 0,
            "raw_material_blank_type": "Extruded",
            "final_part_mass": 201.0,
            "final_part_volume": None,
            "raw_material_mass": 1362.7,
            "raw_material_volume": None,
            "final_part_yield": 0.90,
            "plastic_injection_molding_parts_per_shot": 0,
            "plastic_injection_molding_cycle_time": 0,
            "forging_strikes": 5,
            "forging_trimming_bending_strikes": 0,
            "stamping_steps": 3,
            "heat_treatment_annealing_steps": 0,
            "heat_treatment_annealing_temperature": 0,
            "heat_treatment_tempering_steps": 0,
            "heat_treatment_tempering_temperature": 0,
            "laser_cutting_welding_cycle_time": 0,
            "laser_etching_cycle_time": 0,
            "sanding_cycle_time": 0,
            "machining_cycle_time": 120,
            "anodizing": True,
            "electricity_grid": "Region A",
        },
        "adjustable_params": [
            "material", "recycled_content", "raw_material_blank_type",
            "electricity_grid", "anodizing",
        ],
        "locked_params": [
            "raw_material_mass", "final_part_mass", "final_part_yield",
            "forging_strikes", "stamping_steps", "machining_cycle_time",
        ],
        "allowed_materials": ["Alloy-F", "Alloy-E", "Alloy-B", "Alloy-C"],
        "allowed_blank_types": ["Extruded", "Rolled sheet"],
    },
    {
        "id": "phone_enclosure",
        "product_family": "Phone",
        "component_type": "Enclosure / Structural",
        "display_name": "Smartphone Enclosure (High-Strength Alloy)",
        "description": "Extruded high-strength aluminum enclosure with heavy machining and anodizing",
        "parameters": {
            "material": "Alloy-H",
            "recycled_content": 0,
            "raw_material_blank_type": "Extruded",
            "final_part_mass": 150.0,
            "final_part_volume": None,
            "raw_material_mass": 800.0,
            "raw_material_volume": None,
            "final_part_yield": 0.85,
            "plastic_injection_molding_parts_per_shot": 0,
            "plastic_injection_molding_cycle_time": 0,
            "forging_strikes": 0,
            "forging_trimming_bending_strikes": 0,
            "stamping_steps": 0,
            "heat_treatment_annealing_steps": 0,
            "heat_treatment_annealing_temperature": 0,
            "heat_treatment_tempering_steps": 0,
            "heat_treatment_tempering_temperature": 0,
            "laser_cutting_welding_cycle_time": 0,
            "laser_etching_cycle_time": 0,
            "sanding_cycle_time": 0,
            "machining_cycle_time": 600,
            "anodizing": True,
            "electricity_grid": "Region A",
        },
        "adjustable_params": [
            "material", "recycled_content", "raw_material_blank_type",
            "electricity_grid", "anodizing",
        ],
        "locked_params": [
            "raw_material_mass", "final_part_mass", "machining_cycle_time",
        ],
        "allowed_materials": ["Alloy-H", "Alloy-G", "Alloy-F"],
        "allowed_blank_types": ["Extruded", "Rolled sheet", "Rolled plate >3mm"],
    },
    {
        "id": "wearable_case_polymer",
        "product_family": "Wearable",
        "component_type": "Case / Housing",
        "display_name": "Wearable Case (Polymer)",
        "description": "Injection molded polymer case component",
        "parameters": {
            "material": "Polymer-A",
            "recycled_content": 0,
            "raw_material_blank_type": "Injection molded plastic",
            "final_part_mass": 35.0,
            "final_part_volume": None,
            "raw_material_mass": 200.0,
            "raw_material_volume": None,
            "final_part_yield": 0.92,
            "plastic_injection_molding_parts_per_shot": 10,
            "plastic_injection_molding_cycle_time": 60,
            "forging_strikes": 0,
            "forging_trimming_bending_strikes": 0,
            "stamping_steps": 0,
            "heat_treatment_annealing_steps": 0,
            "heat_treatment_annealing_temperature": 0,
            "heat_treatment_tempering_steps": 0,
            "heat_treatment_tempering_temperature": 0,
            "laser_cutting_welding_cycle_time": 0,
            "laser_etching_cycle_time": 0,
            "sanding_cycle_time": 0,
            "machining_cycle_time": 0,
            "anodizing": False,
            "electricity_grid": "Region A",
        },
        "adjustable_params": [
            "recycled_content", "electricity_grid",
            "plastic_injection_molding_parts_per_shot",
            "plastic_injection_molding_cycle_time",
        ],
        "locked_params": [
            "material", "raw_material_blank_type", "raw_material_mass",
        ],
        "allowed_materials": ["Polymer-A"],
        "allowed_blank_types": ["Injection molded plastic"],
    },
    {
        "id": "wearable_band_metal",
        "product_family": "Wearable",
        "component_type": "Band (Metal)",
        "display_name": "Wearable Band Link (Aluminum)",
        "description": "Rolled sheet aluminum band link with stamping, sanding, and anodizing",
        "parameters": {
            "material": "Alloy-F",
            "recycled_content": 0,
            "raw_material_blank_type": "Rolled sheet",
            "final_part_mass": 20.0,
            "final_part_volume": None,
            "raw_material_mass": 120.0,
            "raw_material_volume": None,
            "final_part_yield": 0.85,
            "plastic_injection_molding_parts_per_shot": 0,
            "plastic_injection_molding_cycle_time": 0,
            "forging_strikes": 0,
            "forging_trimming_bending_strikes": 0,
            "stamping_steps": 5,
            "heat_treatment_annealing_steps": 0,
            "heat_treatment_annealing_temperature": 0,
            "heat_treatment_tempering_steps": 0,
            "heat_treatment_tempering_temperature": 0,
            "laser_cutting_welding_cycle_time": 0,
            "laser_etching_cycle_time": 0,
            "sanding_cycle_time": 60,
            "machining_cycle_time": 0,
            "anodizing": True,
            "electricity_grid": "Region A",
        },
        "adjustable_params": [
            "material", "recycled_content", "electricity_grid", "anodizing",
        ],
        "locked_params": [
            "raw_material_blank_type", "raw_material_mass",
            "stamping_steps", "sanding_cycle_time",
        ],
        "allowed_materials": ["Alloy-F", "Alloy-E", "Alloy-C", "Alloy-A"],
        "allowed_blank_types": ["Rolled sheet"],
    },
    {
        "id": "laptop_enclosure",
        "product_family": "Laptop",
        "component_type": "Enclosure / Structural",
        "display_name": "Laptop Enclosure (Aluminum)",
        "description": "Large extruded aluminum enclosure with heavy machining and anodizing",
        "parameters": {
            "material": "Alloy-F",
            "recycled_content": 0,
            "raw_material_blank_type": "Extruded",
            "final_part_mass": 500.0,
            "final_part_volume": None,
            "raw_material_mass": 2500.0,
            "raw_material_volume": None,
            "final_part_yield": 0.80,
            "plastic_injection_molding_parts_per_shot": 0,
            "plastic_injection_molding_cycle_time": 0,
            "forging_strikes": 0,
            "forging_trimming_bending_strikes": 0,
            "stamping_steps": 0,
            "heat_treatment_annealing_steps": 0,
            "heat_treatment_annealing_temperature": 0,
            "heat_treatment_tempering_steps": 0,
            "heat_treatment_tempering_temperature": 0,
            "laser_cutting_welding_cycle_time": 0,
            "laser_etching_cycle_time": 0,
            "sanding_cycle_time": 0,
            "machining_cycle_time": 900,
            "anodizing": True,
            "electricity_grid": "Region A",
        },
        "adjustable_params": [
            "material", "recycled_content", "raw_material_blank_type",
            "electricity_grid", "anodizing",
        ],
        "locked_params": [
            "raw_material_mass", "final_part_mass", "machining_cycle_time",
        ],
        "allowed_materials": ["Alloy-F", "Alloy-E", "Alloy-C", "Alloy-H"],
        "allowed_blank_types": ["Extruded", "Rolled sheet", "Rolled plate >3mm"],
    },
]

PRESET_MAP: dict[str, dict] = {p["id"]: p for p in BASELINE_PRESETS}


DEMO_SCENARIOS: list[dict] = [
    {
        "id": "demo_phone_housing_recycled",
        "title": "Material swap — 100% recycled aluminum housing",
        "description": "Switch a smartphone's largest metal component to fully recycled aluminum and see the carbon delta.",
        "program": "SP200",
        "component": "Housing",
        "modifications": {"recycled_content": 100},
        "product_group": "Phone",
    },
    {
        "id": "demo_laptop_enclosure_process",
        "title": "Process change — reduced machining time",
        "description": "Cut machining cycle time on a laptop enclosure and watch the process breakdown shift.",
        "program": "LP400",
        "component": "Housing",
        "modifications": {"machining_cycle_time": 120},
        "product_group": "Laptop",
    },
    {
        "id": "demo_laptop_enclosure_renewables",
        "title": "Manufacturing grid — 100% renewable electricity",
        "description": "What if this enclosure were manufactured on a fully renewable grid instead of the default region?",
        "program": "LP400",
        "component": "Housing",
        "modifications": {"electricity_grid": "100% renewables"},
        "product_group": "Laptop",
    },
    {
        "id": "demo_tablet_housing_combined",
        "title": "Combined levers — recycled content + renewable grid",
        "description": "Stack recycled aluminum and a renewable grid on a tablet housing to see combined impact.",
        "program": "TB300",
        "component": "Housing",
        "modifications": {"recycled_content": 100, "electricity_grid": "100% renewables"},
        "product_group": "Tablet",
    },
    {
        "id": "demo_wearable_housing_optimize",
        "title": "Optimizer — lowest-carbon configuration",
        "description": "Let the constrained optimizer search for the lowest-carbon setup for this wearable component.",
        "program": "WR500",
        "component": "Housing",
        "modifications": {},
        "run_optimizer": True,
        "product_group": "Wearable",
    },
]
