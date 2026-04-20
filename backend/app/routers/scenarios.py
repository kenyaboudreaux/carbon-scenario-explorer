from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..models.schemas import ScenarioCreate, ScenarioUpdate, SavedScenario, ScenarioSummary

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummary])
async def list_scenarios(request: Request):
    store = request.app.state.scenario_store
    return store.list_all()


@router.post("", response_model=SavedScenario)
async def create_scenario(req: ScenarioCreate, request: Request):
    store = request.app.state.scenario_store
    data = request.app.state.loaded_data
    return store.create(req, data)


@router.get("/{scenario_id}", response_model=SavedScenario)
async def get_scenario(scenario_id: str, request: Request):
    store = request.app.state.scenario_store
    s = store.get(scenario_id)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return s


@router.put("/{scenario_id}", response_model=SavedScenario)
async def update_scenario(scenario_id: str, req: ScenarioUpdate, request: Request):
    store = request.app.state.scenario_store
    s = store.update(scenario_id, req)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return s


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str, request: Request):
    store = request.app.state.scenario_store
    if not store.delete(scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"ok": True}


class CompareRequest(BaseModel):
    ids: list[str]


@router.post("/compare", response_model=list[SavedScenario])
async def compare_scenarios(req: CompareRequest, request: Request):
    store = request.app.state.scenario_store
    return store.get_multiple(req.ids)
