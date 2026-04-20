"""Category-routed calculator dispatch.

Routes scenario calculations to the correct category-specific calculator
based on component classification. This is the single entry point for
all carbon footprint calculations in the system.
"""

from ...models.schemas import ScenarioInput, ProcessBreakdown
from ..data_loader import LoadedData
from .enclosure import calculate as enclosure_calculate
from .packaging import calculate as packaging_calculate


def calculate_for_category(
    category: str,
    scenario_input: ScenarioInput,
    data: LoadedData,
    packaging_context: dict | None = None,
) -> ProcessBreakdown:
    """Route calculation to the correct category-specific calculator."""
    if category == "packaging" and packaging_context is not None:
        return packaging_calculate(scenario_input, data, packaging_context)

    # Default: enclosure mass-based calculator
    return enclosure_calculate(scenario_input, data)
