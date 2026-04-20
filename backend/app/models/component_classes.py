"""Component classification system for PMF-to-model mapping.

Maps PMF component names to classes, each with constrained materials,
blank types, and typical manufacturing processes.
"""

from enum import Enum


class ComponentClass(str, Enum):
    METAL_STRUCTURAL = "metal_structural"
    POLYMER_HOUSING = "polymer_housing"
    GLASS = "glass"
    SOFT_GOODS = "soft_goods"
    HARDWARE_FASTENER = "hardware_fastener"
    BATTERY = "battery"
    DISPLAY = "display"
    PCB_ELECTRONIC = "pcb_electronic"
    THERMAL = "thermal"
    PACKAGING = "packaging"
    OTHER = "other"


# Map PMF component names to classes (case-sensitive, exact match)
COMPONENT_NAME_RULES: dict[str, ComponentClass] = {
    "Housing": ComponentClass.METAL_STRUCTURAL,
    "Enclosure": ComponentClass.METAL_STRUCTURAL,
    "RIM": ComponentClass.METAL_STRUCTURAL,
    "Trackpad": ComponentClass.METAL_STRUCTURAL,
    "Cover_glass": ComponentClass.GLASS,
    "Back Crystal": ComponentClass.GLASS,
    "Front Crystal": ComponentClass.GLASS,
    "Battery": ComponentClass.BATTERY,
    "Display_assembly": ComponentClass.DISPLAY,
    "MLB": ComponentClass.PCB_ELECTRONIC,
    "Other_PCB": ComponentClass.PCB_ELECTRONIC,
    "Other_flex": ComponentClass.PCB_ELECTRONIC,
    "SSD": ComponentClass.PCB_ELECTRONIC,
    "Wireless": ComponentClass.PCB_ELECTRONIC,
    "I_O": ComponentClass.PCB_ELECTRONIC,
    "FCAM": ComponentClass.PCB_ELECTRONIC,
    "RCAM": ComponentClass.PCB_ELECTRONIC,
    "Depth": ComponentClass.PCB_ELECTRONIC,
    "Optical Module": ComponentClass.PCB_ELECTRONIC,
    "IPD Motor": ComponentClass.HARDWARE_FASTENER,
    "Speaker": ComponentClass.HARDWARE_FASTENER,
    "Taptic": ComponentClass.HARDWARE_FASTENER,
    "Mesa": ComponentClass.HARDWARE_FASTENER,
    "PAM": ComponentClass.HARDWARE_FASTENER,
    "Fasteners": ComponentClass.HARDWARE_FASTENER,
    "Inductive_charger": ComponentClass.PCB_ELECTRONIC,
    "Keyboard": ComponentClass.POLYMER_HOUSING,
    "Thermal_Mgmt": ComponentClass.THERMAL,
    "PSU": ComponentClass.PCB_ELECTRONIC,
}

# Fallback: map dominant material category to class
MATERIAL_CATEGORY_FALLBACK: dict[str, ComponentClass] = {
    "Aluminum": ComponentClass.METAL_STRUCTURAL,
    "Steel": ComponentClass.HARDWARE_FASTENER,
    "Plastic": ComponentClass.POLYMER_HOUSING,
    "Glass": ComponentClass.GLASS,
    "Ceramic": ComponentClass.GLASS,
    "Textile": ComponentClass.SOFT_GOODS,
    "Elements": ComponentClass.OTHER,
    "Graphite": ComponentClass.OTHER,
    "Rare Earths": ComponentClass.OTHER,
    "Uncategorized": ComponentClass.OTHER,
    "Other": ComponentClass.OTHER,
}

# Map PMF materialCategory to model Material enum value
MATERIAL_CATEGORY_TO_MODEL: dict[str, str | None] = {
    "Aluminum": "Alloy-F",
    "Steel": None,         # Not in model — placeholder with warning
    "Plastic": "Polymer-A",
    "Glass": None,          # Not in model
    "Ceramic": None,        # Not in model
    "Ti": None,             # Titanium not in model
    "Textile": "Polymer-B",       # Soft goods approximation
    "Elements": None,       # Sub-element rows, not a material
    "Graphite": None,
    "Rare Earths": None,
    "Uncategorized": None,
    "Other": None,
}

# Per-class constraints and defaults
CLASS_CONSTRAINTS: dict[ComponentClass, dict] = {
    ComponentClass.METAL_STRUCTURAL: {
        "allowed_materials": ["Alloy-F", "Alloy-E", "Alloy-H", "Alloy-C", "Alloy-A", "Cast-A", "Cast-B"],
        "allowed_blank_types": ["Extruded", "Rolled sheet", "Rolled plate >3mm", "Die cast"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {
            "machining_cycle_time": 120,
            "anodizing": True,
        },
        "allowed_processes": [
            "forging", "stamping", "machining", "anodizing",
            "heat_treatment", "laser", "sanding",
        ],
    },
    ComponentClass.POLYMER_HOUSING: {
        "allowed_materials": ["Polymer-A", "Polymer-B", "Polymer-C"],
        "allowed_blank_types": ["Injection molded plastic"],
        "default_material": "Polymer-A",
        "default_blank_type": "Injection molded plastic",
        "typical_processes": {
            "plastic_injection_molding_parts_per_shot": 8,
            "plastic_injection_molding_cycle_time": 45,
        },
        "allowed_processes": ["injection_molding", "sanding"],
    },
    ComponentClass.GLASS: {
        "allowed_materials": ["Alloy-F"],
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": ["laser", "sanding"],
        "model_limitation": "Glass is not directly modeled; aluminum placeholder used for mass-based estimation",
    },
    ComponentClass.SOFT_GOODS: {
        "allowed_materials": ["Polymer-B", "Polymer-C"],
        "allowed_blank_types": ["Injection molded plastic"],
        "default_material": "Polymer-B",
        "default_blank_type": "Injection molded plastic",
        "typical_processes": {
            "plastic_injection_molding_parts_per_shot": 8,
            "plastic_injection_molding_cycle_time": 45,
        },
        "allowed_processes": ["injection_molding"],
    },
    ComponentClass.HARDWARE_FASTENER: {
        "allowed_materials": ["Alloy-E", "Cast-A", "Cast-B", "Alloy-F"],
        "allowed_blank_types": ["Die cast", "Extruded"],
        "default_material": "Alloy-E",
        "default_blank_type": "Die cast",
        "typical_processes": {
            "machining_cycle_time": 30,
        },
        "allowed_processes": ["machining", "stamping", "forging"],
    },
    ComponentClass.BATTERY: {
        "allowed_materials": ["Alloy-F"],
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": [],
        "model_limitation": "Battery chemistry (Li-ion cells) not modeled; only enclosure/structure mass estimated",
    },
    ComponentClass.DISPLAY: {
        "allowed_materials": ["Alloy-F"],
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": ["laser"],
        "model_limitation": "Display panel manufacturing not modeled; structural frame mass only",
    },
    ComponentClass.PCB_ELECTRONIC: {
        "allowed_materials": ["Alloy-F"],
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": [],
        "model_limitation": "PCB/electronic component manufacturing not modeled; raw material mass estimation only",
    },
    ComponentClass.THERMAL: {
        "allowed_materials": ["Alloy-F", "Alloy-E"],
        "allowed_blank_types": ["Extruded", "Die cast"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {
            "machining_cycle_time": 60,
        },
        "allowed_processes": ["machining", "stamping"],
    },
    ComponentClass.PACKAGING: {
        "allowed_materials": ["Alloy-F"],  # placeholder; packaging uses its own material DB
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": [],
        "calculator_override": "packaging",
    },
    ComponentClass.OTHER: {
        "allowed_materials": ["Alloy-F"],
        "allowed_blank_types": ["Extruded"],
        "default_material": "Alloy-F",
        "default_blank_type": "Extruded",
        "typical_processes": {},
        "allowed_processes": [],
        "model_limitation": "Component type not specifically modeled; generic estimation only",
    },
}


def classify_component(
    component_name: str, dominant_material_category: str | None = None
) -> ComponentClass:
    """Classify a PMF component by name, falling back to dominant material."""
    if component_name in COMPONENT_NAME_RULES:
        return COMPONENT_NAME_RULES[component_name]
    if dominant_material_category and dominant_material_category in MATERIAL_CATEGORY_FALLBACK:
        return MATERIAL_CATEGORY_FALLBACK[dominant_material_category]
    return ComponentClass.OTHER


# --- Model Validity ---

MODEL_VALIDITY: dict[ComponentClass, dict] = {
    ComponentClass.METAL_STRUCTURAL: {
        "status": "validated",
        "calculator": "enclosure_mass_based",
        "message": "Validated for mass-based metal manufacturing scenarios using the enclosure calculator.",
    },
    ComponentClass.POLYMER_HOUSING: {
        "status": "validated",
        "calculator": "enclosure_mass_based",
        "message": "Validated for injection-molded polymer parts using the enclosure calculator.",
    },
    ComponentClass.HARDWARE_FASTENER: {
        "status": "validated",
        "calculator": "enclosure_mass_based",
        "message": "Validated for small metal hardware using the enclosure calculator.",
    },
    ComponentClass.THERMAL: {
        "status": "approximate",
        "calculator": "enclosure_mass_based",
        "message": "Approximate. Uses the generic mass-based calculator; thermal management may involve processes not fully captured.",
    },
    ComponentClass.GLASS: {
        "status": "approximate",
        "calculator": "enclosure_mass_based",
        "message": "Approximate. Glass forming is not modeled. Result is a mass-based placeholder.",
    },
    ComponentClass.SOFT_GOODS: {
        "status": "unsupported",
        "calculator": "none",
        "message": "Unsupported. Textiles require a fiber supply-chain calculator not yet implemented.",
    },
    ComponentClass.PCB_ELECTRONIC: {
        "status": "unsupported",
        "calculator": "none",
        "message": "Unsupported. Electronics require an area-based calculator not yet implemented.",
    },
    ComponentClass.BATTERY: {
        "status": "unsupported",
        "calculator": "none",
        "message": "Unsupported. Battery chemistry is not modeled.",
    },
    ComponentClass.DISPLAY: {
        "status": "unsupported",
        "calculator": "none",
        "message": "Unsupported. Display panel manufacturing is not modeled.",
    },
    ComponentClass.PACKAGING: {
        "status": "validated",
        "calculator": "packaging",
        "message": "Validated. Uses the packaging-specific calculator with material GWP and shipping modal split.",
    },
    ComponentClass.OTHER: {
        "status": "approximate",
        "calculator": "enclosure_mass_based",
        "message": "Approximate. Component type not specifically modeled; generic mass-based estimation.",
    },
}


def get_model_validity(component_class: ComponentClass) -> dict:
    return MODEL_VALIDITY.get(component_class, MODEL_VALIDITY[ComponentClass.OTHER])
