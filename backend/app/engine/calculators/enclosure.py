"""Enclosure / mass-based manufacturing calculator.

Wraps the existing calculate_footprint() function.
"""

from ..calculator import calculate_footprint
from ...models.schemas import ScenarioInput, ProcessBreakdown
from ..data_loader import LoadedData


def calculate(scenario_input: ScenarioInput, data: LoadedData) -> ProcessBreakdown:
    return calculate_footprint(scenario_input, data)
