from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ..models.schemas import ScenarioInput, ProcessBreakdown, FormulaTrace
from ..engine.calculator import calculate_footprint, calculate_footprint_debug

router = APIRouter(prefix="/api", tags=["calculate"])


@router.post("/calculate")
async def calculate(
    scenario: ScenarioInput,
    request: Request,
    debug: bool = Query(False, description="Return full formula trace"),
) -> ProcessBreakdown | FormulaTrace:
    data = request.app.state.loaded_data
    if debug:
        return calculate_footprint_debug(scenario, data)
    return calculate_footprint(scenario, data)
