"""Packaging-specific carbon calculator.

Calculates carbon footprint for packaging components using:
  - Material GWP (kg CO2e/kg) lookup by packaging material type
  - Yield and efficiency adjustments
  - Shipping carbon by modal split (air / sea / ground)

This is fundamentally different from the enclosure calculator:
  - Uses packaging-specific material carbon intensities (not alloy CI)
  - Includes shipping carbon (which can dominate by 50x for air vs sea)
  - Does not model manufacturing processes like machining/forging
"""

from ...models.schemas import ScenarioInput, ProcessBreakdown
from ...config import MODEL_VERSION, DATA_VERSION
from ..data_loader import LoadedData


# Packaging material GWP database (kg CO2e/kg)
# Anonymized values based on published LCA literature ranges
PACKAGING_MATERIALS: dict[str, float] = {
    "Corrugate": 0.80,
    "Molded fiber": 4.30,
    "Greyboard (recycled)": 0.65,
    "Paper": 0.50,
    "Paperboard": 0.70,
    "Adhesive": 2.76,
    "Ink": 3.79,
    "LDPE film": 3.79,
    "PET film": 2.91,
    "PP film": 2.40,
    "PC film": 4.49,
    "Foam insert": 7.50,
    "PS part": 13.60,
}

# Shipping carbon densities (kg CO2e per kg shipped)
SHIPPING_DENSITIES: dict[str, float] = {
    "air": 7.84,
    "sea": 0.15,
    "ground": 0.45,
}

# Default modal split (fraction of mass shipped by each mode)
DEFAULT_MODAL_SPLIT = {
    "air": 0.25,
    "sea": 0.02,
    "ground": 0.73,
}


def calculate(
    scenario_input: ScenarioInput,
    data: LoadedData,
    packaging_context: dict,
) -> ProcessBreakdown:
    """Calculate packaging carbon footprint.

    packaging_context fields:
      - packaging_material: str (key into PACKAGING_MATERIALS)
      - yield_pct: float (0-1, default 1.0)
      - efficiency_pct: float (0-1, default 1.0)
      - air_pct: float (0-1)
      - sea_pct: float (0-1)
      - ground_pct: float (0-1)
    """
    mass_g = scenario_input.raw_material_mass
    mass_kg = mass_g / 1000.0

    # Material lookup
    material_name = packaging_context.get("packaging_material", "Corrugate")
    material_gwp = PACKAGING_MATERIALS.get(material_name, 0.80)

    # Yield and efficiency
    yield_pct = packaging_context.get("yield_pct", 1.0)
    efficiency_pct = packaging_context.get("efficiency_pct", 1.0)
    denominator = max(yield_pct * efficiency_pct, 0.01)
    mass_mobilized_kg = mass_kg / denominator

    # Material carbon
    material_carbon = mass_mobilized_kg * material_gwp

    # Shipping carbon (modal split)
    air_pct = packaging_context.get("air_pct", DEFAULT_MODAL_SPLIT["air"])
    sea_pct = packaging_context.get("sea_pct", DEFAULT_MODAL_SPLIT["sea"])
    ground_pct = packaging_context.get("ground_pct", DEFAULT_MODAL_SPLIT["ground"])

    shipping_carbon = mass_kg * (
        air_pct * SHIPPING_DENSITIES["air"]
        + sea_pct * SHIPPING_DENSITIES["sea"]
        + ground_pct * SHIPPING_DENSITIES["ground"]
    )

    total = material_carbon + shipping_carbon

    # Map into ProcessBreakdown using available fields
    # raw_material = material carbon, upstream_processing = shipping carbon
    result = ProcessBreakdown()
    result.raw_material = material_carbon
    result.upstream_processing = shipping_carbon
    result.total = total
    result.model_version = MODEL_VERSION
    result.data_version = DATA_VERSION
    result.assumptions_hash = data.assumptions_hash

    return result
