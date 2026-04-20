from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

from ..models.schemas import ScenarioInput, ProcessBreakdown
from ..engine.calculators.packaging import calculate, PACKAGING_MATERIALS, SHIPPING_DENSITIES

router = APIRouter(prefix="/api/packaging", tags=["packaging"])


class PackagingCalculateRequest(BaseModel):
    raw_material_mass: float = Field(gt=0, description="Packaging component mass in grams")
    packaging_material: str = "Corrugate"
    yield_pct: float = Field(default=1.0, ge=0.01, le=1.0)
    efficiency_pct: float = Field(default=1.0, ge=0.01, le=1.0)
    air_pct: float = Field(default=0.25, ge=0, le=1)
    sea_pct: float = Field(default=0.02, ge=0, le=1)
    ground_pct: float = Field(default=0.73, ge=0, le=1)


@router.get("/materials")
async def list_packaging_materials():
    """List available packaging materials with their GWP values."""
    return [
        {"name": name, "gwp_kg_co2e_per_kg": gwp}
        for name, gwp in sorted(PACKAGING_MATERIALS.items(), key=lambda x: x[0])
    ]


@router.get("/shipping-modes")
async def list_shipping_modes():
    """List shipping modes with their carbon densities."""
    return [
        {"mode": mode, "density_kg_co2e_per_kg": density}
        for mode, density in SHIPPING_DENSITIES.items()
    ]


@router.post("/calculate", response_model=ProcessBreakdown)
async def calculate_packaging(req: PackagingCalculateRequest, request: Request):
    """Calculate packaging-specific carbon footprint."""
    data = request.app.state.loaded_data

    # Build a minimal ScenarioInput for the packaging calculator
    scenario_input = ScenarioInput(
        material="Alloy-F",  # placeholder; packaging uses its own material DB
        recycled_content=0,
        raw_material_blank_type="Extruded",
        raw_material_mass=req.raw_material_mass,
    )

    packaging_context = {
        "packaging_material": req.packaging_material,
        "yield_pct": req.yield_pct,
        "efficiency_pct": req.efficiency_pct,
        "air_pct": req.air_pct,
        "sea_pct": req.sea_pct,
        "ground_pct": req.ground_pct,
    }

    return calculate(scenario_input, data, packaging_context)
