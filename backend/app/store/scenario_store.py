"""In-memory scenario store with JSON file persistence."""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from ..config import SCENARIOS_FILE
from ..models.schemas import (
    SavedScenario,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioSummary,
    ProcessBreakdown,
)
from ..engine.calculator import calculate_footprint
from ..engine.data_loader import LoadedData


class ScenarioStore:
    def __init__(self, persistence_path: Path | None = None):
        self._path = persistence_path if persistence_path is not None else SCENARIOS_FILE
        self._scenarios: dict[str, SavedScenario] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            for item in raw:
                s = SavedScenario(**item)
                self._scenarios[s.id] = s

    def _save_to_disk(self):
        try:
            items = [s.model_dump() for s in self._scenarios.values()]
            self._path.write_text(json.dumps(items, indent=2, default=str))
        except OSError:
            pass  # Read-only filesystem; fall back to in-memory store

    def list_all(self) -> list[ScenarioSummary]:
        return [
            ScenarioSummary(
                id=s.id,
                name=s.name,
                total=s.breakdown.total,
                material=s.input.material.value,
                recycled_content=s.input.recycled_content,
                created_at=s.created_at,
                product_family=s.product_context.product_family if s.product_context else None,
                component_type=s.product_context.component_type if s.product_context else None,
                part_name=s.product_context.part_name if s.product_context else None,
                origin=s.origin,
            )
            for s in sorted(
                self._scenarios.values(), key=lambda x: x.created_at, reverse=True
            )
        ]

    def get(self, scenario_id: str) -> SavedScenario | None:
        return self._scenarios.get(scenario_id)

    def create(self, req: ScenarioCreate, data: LoadedData) -> SavedScenario:
        breakdown = calculate_footprint(req.input, data)
        now = datetime.now(timezone.utc).isoformat()
        scenario = SavedScenario(
            id=str(uuid.uuid4()),
            name=req.name,
            input=req.input,
            breakdown=breakdown,
            product_context=req.product_context,
            notes=req.notes,
            created_at=now,
            updated_at=now,
            model_version=breakdown.model_version,
            data_version=breakdown.data_version,
            assumptions_hash=breakdown.assumptions_hash,
            origin=req.origin,
        )
        self._scenarios[scenario.id] = scenario
        self._save_to_disk()
        return scenario

    def update(self, scenario_id: str, req: ScenarioUpdate) -> SavedScenario | None:
        s = self._scenarios.get(scenario_id)
        if not s:
            return None
        if req.name is not None:
            s.name = req.name
        if req.notes is not None:
            s.notes = req.notes
        s.updated_at = datetime.now(timezone.utc).isoformat()
        self._scenarios[scenario_id] = s
        self._save_to_disk()
        return s

    def delete(self, scenario_id: str) -> bool:
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            self._save_to_disk()
            return True
        return False

    def get_multiple(self, ids: list[str]) -> list[SavedScenario]:
        return [self._scenarios[i] for i in ids if i in self._scenarios]
