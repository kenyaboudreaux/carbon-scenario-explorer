import csv
import io

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    ids: list[str]


class DiffExportRequest(BaseModel):
    baseline_id: str
    comparison_ids: list[str]


def _product_label(s) -> str:
    ctx = s.product_context
    if ctx and ctx.part_name:
        return ctx.part_name
    if ctx and ctx.product_family and ctx.component_type:
        return f"{ctx.product_family} {ctx.component_type}"
    return ""


def _export_filename(scenarios) -> str:
    for s in scenarios:
        label = _product_label(s)
        if label:
            slug = label.lower().replace(" ", "_").replace("/", "_")[:40]
            return f"{slug}_scenarios_export.csv"
    return "scenarios_export.csv"


@router.post("/csv")
async def export_csv(req: ExportRequest, request: Request):
    store = request.app.state.scenario_store
    scenarios = store.get_multiple(req.ids)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Product Family", "Component Type", "Part Name",
        "Scenario Name", "Origin",
        "Material", "Recycled Content (%)", "Blank Type",
        "Raw Material Mass (g)", "Final Part Yield",
        "Electricity Grid",
        "Forging Strikes", "Stamping Steps",
        "Machining Cycle Time (s)", "Anodizing",
        "Raw Material (kg CO2e)", "Upstream (kg CO2e)",
        "Forging (kg CO2e)", "Stamping (kg CO2e)",
        "Heat Treatment (kg CO2e)", "Machining (kg CO2e)",
        "Laser (kg CO2e)", "Sanding (kg CO2e)",
        "Die Casting (kg CO2e)", "Injection Molding (kg CO2e)",
        "Anodizing (kg CO2e)", "Total (kg CO2e)",
        "Model Version", "Data Version",
    ])

    for s in scenarios:
        inp = s.input
        b = s.breakdown
        ctx = s.product_context
        writer.writerow([
            ctx.product_family if ctx else "",
            ctx.component_type if ctx else "",
            ctx.part_name if ctx else "",
            s.name, s.origin,
            inp.material.value, inp.recycled_content, inp.raw_material_blank_type.value,
            inp.raw_material_mass, inp.final_part_yield,
            inp.electricity_grid.value,
            inp.forging_strikes, inp.stamping_steps,
            inp.machining_cycle_time, inp.anodizing,
            round(b.raw_material, 6), round(b.upstream_processing, 6),
            round(b.forging, 6), round(b.stamping, 6),
            round(b.heat_treatment, 6), round(b.machining, 6),
            round(b.laser, 6), round(b.sanding, 6),
            round(b.die_casting, 6), round(b.injection_molding, 6),
            round(b.anodizing, 6), round(b.total, 6),
            s.model_version, s.data_version,
        ])

    output.seek(0)
    filename = _export_filename(scenarios)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


PROCESS_FIELDS = [
    "raw_material", "upstream_processing", "forging", "stamping",
    "heat_treatment", "machining", "laser", "sanding",
    "die_casting", "injection_molding", "anodizing", "total",
]

PARAM_FIELDS = [
    "material", "recycled_content", "raw_material_blank_type",
    "raw_material_mass", "final_part_yield", "electricity_grid",
    "forging_strikes", "stamping_steps", "machining_cycle_time", "anodizing",
]


@router.post("/diff-csv")
async def export_diff_csv(req: DiffExportRequest, request: Request):
    store = request.app.state.scenario_store
    baseline = store.get(req.baseline_id)
    if not baseline:
        raise HTTPException(404, "Baseline scenario not found")
    comparisons = store.get_multiple(req.comparison_ids)
    if not comparisons:
        raise HTTPException(404, "No comparison scenarios found")

    output = io.StringIO()
    writer = csv.writer(output)

    header = ["Parameter", f"Baseline: {baseline.name}"]
    for c in comparisons:
        header.extend([c.name, f"Delta vs {c.name}"])
    writer.writerow(header)

    # Product context row
    writer.writerow(["Product", _product_label(baseline)] +
                     [_product_label(c) for c in comparisons for _ in range(2)])

    # Parameter rows
    base_dict = baseline.input.model_dump()
    for field in PARAM_FIELDS:
        row = [field, str(base_dict[field])]
        for c in comparisons:
            c_dict = c.input.model_dump()
            cv = str(c_dict[field])
            diff = "" if cv == str(base_dict[field]) else "CHANGED"
            row.extend([cv, diff])
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(["--- Results ---"])

    # Breakdown rows
    base_bd = baseline.breakdown.model_dump()
    for field in PROCESS_FIELDS:
        row = [field, round(base_bd[field], 6)]
        for c in comparisons:
            c_bd = c.breakdown.model_dump()
            cv = round(c_bd[field], 6)
            delta = round(cv - base_bd[field], 6)
            row.extend([cv, delta])
        writer.writerow(row)

    output.seek(0)
    label = _product_label(baseline)
    slug = label.lower().replace(" ", "_").replace("/", "_")[:30] if label else "scenario"
    filename = f"{slug}_diff_export.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
