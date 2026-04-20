import csv
import io

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..engine.pmf_loader import pmf_product_to_dict
from ..engine.pmf_mapper import map_pmf_component, generate_mapping_report, compute_product_impact
from ..models.schemas import ScenarioInput
from ..models.component_classes import classify_component, CLASS_CONSTRAINTS, get_model_validity

router = APIRouter(prefix="/api/pmf", tags=["pmf"])


@router.get("/products")
async def list_pmf_products(request: Request):
    """List all PMF products with summary info."""
    pmf = request.app.state.pmf_data
    return [
        {
            "program": p.program,
            "name": p.name,
            "product_group": p.product_group,
            "total_mass_g": round(p.total_mass_shipped_g, 2),
            "recycled_content_pct": p.recycled_content_pct,
            "component_count": len(p.components),
            "is_common_parts": p.is_common_parts,
        }
        for p in sorted(pmf.values(), key=lambda x: (x.product_group, x.name))
    ]


@router.get("/products/{program}")
async def get_pmf_product(program: str, request: Request):
    """Get full PMF product detail with component breakdown."""
    pmf = request.app.state.pmf_data
    product = pmf.get(program)
    if not product:
        raise HTTPException(404, f"PMF product '{program}' not found")
    return pmf_product_to_dict(product)


@router.get("/products/{program}/components/{component}")
async def get_pmf_component(program: str, component: str, request: Request):
    """Get a specific component's material breakdown."""
    pmf = request.app.state.pmf_data
    product = pmf.get(program)
    if not product:
        raise HTTPException(404, f"PMF product '{program}' not found")
    comp = product.components.get(component)
    if not comp:
        raise HTTPException(404, f"Component '{component}' not found in {program}")
    return {
        "program": program,
        "product_name": product.name,
        "product_group": product.product_group,
        "component": comp.component,
        "subcomponents": comp.subcomponents,
        "total_mass_shipped_g": round(comp.total_mass_shipped_g, 4),
        "recycled_content_pct": comp.recycled_content_pct,
        "dominant_material_category": comp.dominant_material_category,
        "material_breakdown": {
            k: round(v, 4) for k, v in sorted(
                comp.material_breakdown.items(), key=lambda x: -x[1]
            ) if v > 0.0001
        },
    }


@router.get("/groups")
async def list_pmf_groups(request: Request):
    """List product groups with their products."""
    pmf = request.app.state.pmf_data
    groups: dict[str, list] = {}
    for p in pmf.values():
        if p.product_group not in groups:
            groups[p.product_group] = []
        groups[p.product_group].append({
            "program": p.program,
            "name": p.name,
            "total_mass_g": round(p.total_mass_shipped_g, 2),
            "component_count": len(p.components),
        })
    return groups


class MapComponentRequest(BaseModel):
    program: str
    component: str


@router.post("/map-component")
async def map_component(req: MapComponentRequest, request: Request):
    """Map a PMF component to ScenarioInput with full provenance tracking."""
    pmf = request.app.state.pmf_data
    product = pmf.get(req.program)
    if not product:
        raise HTTPException(404, f"PMF product '{req.program}' not found")
    comp = product.components.get(req.component)
    if not comp:
        raise HTTPException(404, f"Component '{req.component}' not found in {req.program}")

    result = map_pmf_component(product, comp)
    from ..models.component_classes import ComponentClass
    comp_class = ComponentClass(result.component_class) if result.component_class in [c.value for c in ComponentClass] else ComponentClass.OTHER
    validity = get_model_validity(comp_class)
    return {
        "scenario_input": result.scenario_input,
        "provenance": result.provenance,
        "component_class": result.component_class,
        "warnings": result.warnings,
        "confidence_score": result.confidence_score,
        "product_name": product.name,
        "product_group": product.product_group,
        "model_validity": validity,
    }


@router.get("/mapping-report")
async def get_mapping_report(request: Request):
    """Full mapping audit report for all PMF products."""
    pmf = request.app.state.pmf_data
    return generate_mapping_report(pmf)


@router.post("/mapping-report/csv")
async def export_mapping_report_csv(request: Request):
    """Download mapping report as CSV."""
    pmf = request.app.state.pmf_data
    report = generate_mapping_report(pmf)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Program", "Product Name", "Product Group", "Component",
        "Mass (g)", "Source Material Category", "Mapped Model Material",
        "Source RC%", "Mapped RC Bucket", "RC Snap Distance",
        "Component Class", "Confidence", "Warnings",
    ])

    for prod in report["products"]:
        for comp in prod["components"]:
            writer.writerow([
                prod["program"], prod["name"], prod["product_group"],
                comp["component"], comp["mass_g"],
                comp["source_material_category"], comp["mapped_model_material"],
                comp["source_recycled_content_pct"], comp["mapped_recycled_content_bucket"],
                comp["rc_snap_distance"], comp["component_class"],
                comp["confidence"], "; ".join(comp["warnings"]) if comp["warnings"] else "",
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pmf_mapping_report.csv"},
    )


class ProductImpactRequest(BaseModel):
    program: str
    component: str
    scenario_input: ScenarioInput


@router.post("/product-impact")
async def get_product_impact(req: ProductImpactRequest, request: Request):
    """Compute product-level impact of modifying a component scenario."""
    pmf = request.app.state.pmf_data
    data = request.app.state.loaded_data
    product = pmf.get(req.program)
    if not product:
        raise HTTPException(404, f"PMF product '{req.program}' not found")
    if req.component not in product.components:
        raise HTTPException(404, f"Component '{req.component}' not found in {req.program}")
    return compute_product_impact(product, req.component, req.scenario_input, data)


@router.get("/coverage")
async def get_coverage(request: Request):
    """PMF coverage and confidence summary."""
    pmf = request.app.state.pmf_data
    report = generate_mapping_report(pmf)

    # Identify components with model limitations
    unmappable = []
    for prod in report["products"]:
        for comp in prod["components"]:
            cls = comp["component_class"]
            constraints = CLASS_CONSTRAINTS.get(classify_component(comp["component"]), {})
            if constraints.get("model_limitation"):
                unmappable.append({
                    "program": prod["program"],
                    "component": comp["component"],
                    "reason": constraints["model_limitation"],
                })

    return {
        "pmf_backed_products": report["total_products"],
        "preset_only_products": 8,
        "excluded_products": [
            {"program": "N217", "reason": "Unrealistic mass value (data corruption)", "file": "N217_Common parts_PMF_2026_04_17.csv"},
        ],
        "total_components": report["total_components"],
        "components_with_limitations": len(unmappable),
        "confidence_summary": report["mapping_summary"],
        "material_coverage": report["material_coverage"],
        "warning_count": report["warning_count"],
    }
