from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from ..models.schemas import ScenarioInput, OptimizationResult
from ..engine.optimizer import optimize_scenario

router = APIRouter(prefix="/api", tags=["optimize"])


class OptimizeRequest(BaseModel):
    input: ScenarioInput
    preset_id: Optional[str] = None


@router.post("/optimize", response_model=OptimizationResult)
async def optimize(req: OptimizeRequest, request: Request):
    data = request.app.state.loaded_data
    return optimize_scenario(req.input, req.preset_id, data)
