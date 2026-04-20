"""Constrained heuristic optimizer for carbon footprint reduction (V1 Beta).

Strategy (ordered by typical impact):
1. Switch grid to 100% renewables
2. Maximize recycled content
3. Try allowed material substitutions for lower carbon intensity
4. Try allowed blank type substitutions for lower upstream
"""

from ..models.schemas import ScenarioInput, ProcessBreakdown, ParameterDiff, OptimizationResult
from ..models.enums import Material, BlankType, ElectricityGrid, VALID_RECYCLED_CONTENT, ALL_RECYCLED_CONTENT
from ..models.products import PRESET_MAP
from .calculator import calculate_footprint
from .data_loader import LoadedData


# Default rules when no preset is specified
DEFAULT_ADJUSTABLE = ["material", "recycled_content", "electricity_grid", "raw_material_blank_type", "anodizing"]
DEFAULT_LOCKED = [
    "raw_material_mass", "final_part_mass", "final_part_yield",
    "forging_strikes", "forging_trimming_bending_strikes", "stamping_steps",
    "heat_treatment_annealing_steps", "heat_treatment_annealing_temperature",
    "heat_treatment_tempering_steps", "heat_treatment_tempering_temperature",
    "machining_cycle_time", "laser_cutting_welding_cycle_time",
    "laser_etching_cycle_time", "sanding_cycle_time",
    "plastic_injection_molding_parts_per_shot", "plastic_injection_molding_cycle_time",
]


def optimize_scenario(
    baseline: ScenarioInput,
    preset_id: str | None,
    data: LoadedData,
) -> OptimizationResult:
    preset = PRESET_MAP.get(preset_id) if preset_id else None
    adjustable = set(preset["adjustable_params"] if preset else DEFAULT_ADJUSTABLE)
    allowed_materials = preset["allowed_materials"] if preset else [m.value for m in Material]
    allowed_blank_types = preset["allowed_blank_types"] if preset else [b.value for b in BlankType]
    constraints_applied: list[str] = []

    baseline_bd = calculate_footprint(baseline, data)
    best_input = baseline.model_copy()
    best_total = baseline_bd.total

    # Track individual changes that improved things
    applied_changes: list[tuple[str, object, object]] = []

    # 1. Grid switch to renewables
    if "electricity_grid" in adjustable and baseline.electricity_grid != ElectricityGrid.RENEWABLES:
        candidate = best_input.model_copy(update={"electricity_grid": ElectricityGrid.RENEWABLES})
        bd = calculate_footprint(candidate, data)
        if bd.total < best_total:
            applied_changes.append(("electricity_grid", best_input.electricity_grid.value, "100% renewables"))
            best_input = candidate
            best_total = bd.total
            constraints_applied.append("Switched to 100% renewables grid")

    # 2. Maximize recycled content
    if "recycled_content" in adjustable:
        mat_val = best_input.material
        valid_rcs = VALID_RECYCLED_CONTENT.get(mat_val, ALL_RECYCLED_CONTENT)
        for rc in sorted(valid_rcs, reverse=True):
            if rc <= best_input.recycled_content:
                break
            candidate = best_input.model_copy(update={"recycled_content": rc})
            bd = calculate_footprint(candidate, data)
            if bd.total < best_total:
                applied_changes.append(("recycled_content", best_input.recycled_content, rc))
                best_input = candidate
                best_total = bd.total
                constraints_applied.append(f"Increased recycled content to {rc}%")
                break

    # 3. Material substitution — try each allowed material at highest RC
    if "material" in adjustable:
        current_mat = best_input.material.value
        for mat_str in allowed_materials:
            if mat_str == current_mat:
                continue
            try:
                mat_enum = Material(mat_str)
            except ValueError:
                continue
            valid_rcs = VALID_RECYCLED_CONTENT.get(mat_enum, ALL_RECYCLED_CONTENT)
            best_rc = max(valid_rcs)
            try:
                candidate = best_input.model_copy(update={
                    "material": mat_enum,
                    "recycled_content": best_rc,
                })
                bd = calculate_footprint(candidate, data)
                if bd.total < best_total:
                    old_mat = best_input.material.value
                    old_rc = best_input.recycled_content
                    applied_changes.append(("material", old_mat, mat_str))
                    if old_rc != best_rc:
                        applied_changes.append(("recycled_content", old_rc, best_rc))
                    best_input = candidate
                    best_total = bd.total
                    constraints_applied.append(f"Substituted material to {mat_str} at {best_rc}% RC")
            except Exception:
                continue

    # 4. Blank type substitution
    if "raw_material_blank_type" in adjustable:
        current_bt = best_input.raw_material_blank_type.value
        for bt_str in allowed_blank_types:
            if bt_str == current_bt:
                continue
            try:
                bt_enum = BlankType(bt_str)
                candidate = best_input.model_copy(update={"raw_material_blank_type": bt_enum})
                bd = calculate_footprint(candidate, data)
                if bd.total < best_total:
                    applied_changes.append(("raw_material_blank_type", current_bt, bt_str))
                    best_input = candidate
                    best_total = bd.total
                    constraints_applied.append(f"Changed blank type to {bt_str}")
            except Exception:
                continue

    # Build diffs
    optimized_bd = calculate_footprint(best_input, data)
    baseline_dict = baseline.model_dump()
    optimized_dict = best_input.model_dump()
    diffs: list[ParameterDiff] = []

    for key in baseline_dict:
        bv = baseline_dict[key]
        ov = optimized_dict[key]
        if bv != ov:
            diffs.append(ParameterDiff(
                parameter=key,
                before=bv if not isinstance(bv, bool) else bv,
                after=ov if not isinstance(ov, bool) else ov,
                impact_direction="lower",
            ))

    reduction_kg = baseline_bd.total - optimized_bd.total
    reduction_pct = (reduction_kg / baseline_bd.total * 100) if baseline_bd.total > 0 else 0.0

    if not constraints_applied:
        constraints_applied.append("No further optimization found within constraints")

    return OptimizationResult(
        baseline_breakdown=baseline_bd,
        optimized_input=best_input,
        optimized_breakdown=optimized_bd,
        total_reduction_kg=round(reduction_kg, 6),
        total_reduction_pct=round(reduction_pct, 2),
        parameter_diffs=diffs,
        constraints_applied=constraints_applied,
    )
