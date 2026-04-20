from fastapi import APIRouter, HTTPException, Request

from ..models.enums import Material, BlankType, ElectricityGrid, VALID_RECYCLED_CONTENT, ALL_RECYCLED_CONTENT
from ..models.schemas import ScenarioInput
from ..models.parameter_contract import PARAMETER_CONTRACT
from ..models.products import (
    ProductFamily, ComponentType, FAMILY_COMPONENTS,
    BASELINE_PRESETS, PRESET_MAP, DEMO_SCENARIOS,
)

router = APIRouter(prefix="/api/reference", tags=["reference"])


@router.get("/materials")
async def get_materials(request: Request):
    data = request.app.state.loaded_data
    result = []
    for mat in Material:
        valid_rc = VALID_RECYCLED_CONTENT.get(mat, ALL_RECYCLED_CONTENT)
        intensities = {}
        ci_map = data.alloy_carbon_intensity.get(mat.value, {})
        for rc in valid_rc:
            rc_key = f"{rc}%"
            if rc_key in ci_map:
                intensities[rc] = ci_map[rc_key]
        result.append({
            "value": mat.value,
            "valid_recycled_content": valid_rc,
            "carbon_intensities": intensities,
        })
    return result


@router.get("/grid-options")
async def get_grid_options(request: Request):
    data = request.app.state.loaded_data
    return [
        {"value": g.value, "intensity": data.grid_intensities.get(g.value, 0)}
        for g in ElectricityGrid
    ]


@router.get("/blank-types")
async def get_blank_types():
    return [{"value": bt.value} for bt in BlankType]


@router.get("/defaults")
async def get_defaults():
    default = ScenarioInput(
        material=Material.ALLOY_F,
        recycled_content=0,
        raw_material_blank_type=BlankType.EXTRUDED,
        raw_material_mass=1000.0,
        electricity_grid=ElectricityGrid.REGION_A,
    )
    return default.model_dump()


@router.get("/parameter-contract")
async def get_parameter_contract():
    return PARAMETER_CONTRACT


@router.get("/footprints")
async def list_footprints(request: Request):
    data = request.app.state.loaded_data
    return list(data.footprint_data.keys())


@router.get("/footprints/{product_key}")
async def get_footprint(product_key: str, request: Request):
    data = request.app.state.loaded_data
    df = data.footprint_data.get(product_key)
    if df is None:
        return {"error": f"Footprint '{product_key}' not found"}
    return df.to_dict(orient="records")


@router.get("/product-families")
async def get_product_families():
    return [{"value": f.value, "component_types": FAMILY_COMPONENTS.get(f.value, [])}
            for f in ProductFamily]


@router.get("/component-types")
async def get_component_types():
    return [{"value": c.value} for c in ComponentType]


@router.get("/presets")
async def get_presets():
    return [
        {
            "id": p["id"],
            "display_name": p["display_name"],
            "product_family": p["product_family"],
            "component_type": p["component_type"],
            "description": p["description"],
        }
        for p in BASELINE_PRESETS
    ]


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    preset = PRESET_MAP.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return preset


@router.get("/demo-scenarios")
async def get_demo_scenarios():
    return DEMO_SCENARIOS
