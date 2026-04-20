"""PMF-to-model mapping engine with field-level provenance tracking."""

from dataclasses import dataclass, field
from typing import Any

from ..models.schemas import ScenarioInput
from ..models.enums import Material, BlankType, ElectricityGrid, VALID_RECYCLED_CONTENT, ALL_RECYCLED_CONTENT
from ..models.component_classes import (
    ComponentClass, CLASS_CONSTRAINTS, MATERIAL_CATEGORY_TO_MODEL,
    classify_component,
)
from .pmf_loader import PMFProduct, PMFComponent


@dataclass
class FieldProvenance:
    value: Any
    source: str       # "pmf_imported" | "pmf_inferred" | "class_default" | "model_default"
    confidence: str   # "high" | "medium" | "low"
    notes: str = ""


@dataclass
class MappingResult:
    scenario_input: dict           # ScenarioInput as dict (for JSON serialization)
    provenance: dict[str, dict]    # field_name → {value, source, confidence, notes}
    component_class: str
    warnings: list[str] = field(default_factory=list)
    confidence_score: float = 0.0


def _snap_rc_to_bucket(rc_pct: float, valid_buckets: list[int]) -> tuple[int, float]:
    """Snap a floating-point recycled content % to the nearest valid bucket.
    Returns (bucket, snap_distance)."""
    if not valid_buckets:
        return 0, rc_pct
    best = min(valid_buckets, key=lambda b: abs(b - rc_pct))
    return best, abs(best - rc_pct)


def _map_material(
    dominant_category: str | None, comp_class: ComponentClass
) -> tuple[str, str, str, str]:
    """Map PMF dominant material category to model material.
    Returns (material_value, source, confidence, notes)."""
    constraints = CLASS_CONSTRAINTS[comp_class]

    # Try direct category mapping
    if dominant_category and dominant_category in MATERIAL_CATEGORY_TO_MODEL:
        model_mat = MATERIAL_CATEGORY_TO_MODEL[dominant_category]
        if model_mat and model_mat in constraints["allowed_materials"]:
            return model_mat, "pmf_inferred", "medium", f"Mapped from PMF category '{dominant_category}'"
        if model_mat:
            # Material exists in model but not allowed for this class — use class default
            return (
                constraints["default_material"], "class_default", "low",
                f"PMF category '{dominant_category}' maps to '{model_mat}' "
                f"but not allowed for {comp_class.value}; using class default"
            )
        # Category has no model equivalent
        return (
            constraints["default_material"], "class_default", "low",
            f"PMF category '{dominant_category}' has no model equivalent; "
            f"using {constraints['default_material']} placeholder"
        )

    return constraints["default_material"], "class_default", "low", "No PMF material category; using class default"


def map_pmf_component(
    product: PMFProduct, component: PMFComponent
) -> MappingResult:
    """Map a PMF component to a ScenarioInput with full provenance tracking."""
    warnings: list[str] = []
    provenance: dict[str, dict] = {}

    # Classify the component
    comp_class = classify_component(
        component.component, component.dominant_material_category
    )
    constraints = CLASS_CONSTRAINTS[comp_class]

    # Check for model limitations
    limitation = constraints.get("model_limitation")
    if limitation:
        warnings.append(f"{component.component}: {limitation}")

    # --- Field-by-field mapping ---

    # 1. raw_material_mass (direct import from PMF)
    mass = max(component.total_mass_shipped_g, 0.1)
    provenance["raw_material_mass"] = {
        "value": round(mass, 4), "source": "pmf_imported", "confidence": "high",
        "notes": f"Total shipped mass from PMF: {component.total_mass_shipped_g:.4f}g",
    }

    # 2. material (inferred from PMF category + class)
    mat_val, mat_src, mat_conf, mat_notes = _map_material(
        component.dominant_material_category, comp_class
    )
    if mat_src == "class_default" and component.dominant_material_category:
        cat = component.dominant_material_category
        if cat in ("Steel", "Glass", "Ceramic", "Ti", "Graphite", "Rare Earths"):
            warnings.append(
                f"'{cat}' components cannot be modeled directly in the current model; "
                f"using '{mat_val}' as placeholder. Carbon estimate will be approximate."
            )
    provenance["material"] = {
        "value": mat_val, "source": mat_src, "confidence": mat_conf, "notes": mat_notes,
    }

    # 3. recycled_content (snapped from PMF)
    try:
        mat_enum = Material(mat_val)
        valid_rcs = VALID_RECYCLED_CONTENT.get(mat_enum, ALL_RECYCLED_CONTENT)
    except ValueError:
        valid_rcs = ALL_RECYCLED_CONTENT
    rc_bucket, rc_distance = _snap_rc_to_bucket(component.recycled_content_pct, valid_rcs)
    rc_conf = "high" if rc_distance <= 5 else "medium" if rc_distance <= 15 else "low"
    rc_notes = f"PMF: {component.recycled_content_pct:.1f}% → bucket {rc_bucket}% (distance: {rc_distance:.1f}pp)"
    if rc_distance > 10:
        warnings.append(
            f"Recycled content snapped by {rc_distance:.1f} percentage points "
            f"({component.recycled_content_pct:.1f}% → {rc_bucket}%)"
        )
    provenance["recycled_content"] = {
        "value": rc_bucket, "source": "pmf_imported", "confidence": rc_conf, "notes": rc_notes,
    }

    # 4. raw_material_blank_type (class default)
    bt_val = constraints["default_blank_type"]
    provenance["raw_material_blank_type"] = {
        "value": bt_val, "source": "class_default", "confidence": "medium",
        "notes": f"Default for {comp_class.value} class",
    }

    # 5. electricity_grid (model default — no PMF data)
    provenance["electricity_grid"] = {
        "value": "Region A", "source": "model_default", "confidence": "low",
        "notes": "No manufacturing location in PMF data; defaulting to China",
    }

    # 6. Process parameters from class typical_processes
    typical = constraints.get("typical_processes", {})
    process_fields = [
        "forging_strikes", "forging_trimming_bending_strikes", "stamping_steps",
        "heat_treatment_annealing_steps", "heat_treatment_annealing_temperature",
        "heat_treatment_tempering_steps", "heat_treatment_tempering_temperature",
        "machining_cycle_time", "laser_cutting_welding_cycle_time",
        "laser_etching_cycle_time", "sanding_cycle_time",
        "plastic_injection_molding_parts_per_shot",
        "plastic_injection_molding_cycle_time", "anodizing",
    ]
    for pf in process_fields:
        if pf in typical:
            provenance[pf] = {
                "value": typical[pf], "source": "class_default", "confidence": "low",
                "notes": f"Typical for {comp_class.value} class",
            }
        else:
            default_val = False if pf == "anodizing" else 0
            provenance[pf] = {
                "value": default_val, "source": "model_default", "confidence": "low",
                "notes": "No PMF or class data; model default",
            }

    # 7. Informational / geometry fields
    provenance["final_part_mass"] = {
        "value": None, "source": "model_default", "confidence": "low",
        "notes": "Not available in PMF data",
    }
    provenance["final_part_volume"] = {
        "value": None, "source": "model_default", "confidence": "low",
        "notes": "Not available in PMF data",
    }
    provenance["raw_material_volume"] = {
        "value": None, "source": "model_default", "confidence": "low",
        "notes": "Not available in PMF data",
    }
    provenance["final_part_yield"] = {
        "value": 0.90, "source": "model_default", "confidence": "low",
        "notes": "Standard default; PMF does not provide yield data",
    }

    # Build ScenarioInput dict
    input_dict = {
        "material": mat_val,
        "recycled_content": rc_bucket,
        "raw_material_blank_type": bt_val,
        "raw_material_mass": round(mass, 4),
        "final_part_mass": None,
        "final_part_volume": None,
        "raw_material_volume": None,
        "final_part_yield": 0.90,
        "electricity_grid": "Region A",
        "anodizing": typical.get("anodizing", False),
    }
    for pf in process_fields:
        if pf not in input_dict:
            input_dict[pf] = typical.get(pf, False if pf == "anodizing" else 0)

    # Confidence score: weighted average
    conf_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
    weights = {"raw_material_mass": 3, "material": 2, "recycled_content": 2,
               "raw_material_blank_type": 1, "electricity_grid": 1}
    total_w = 0
    total_score = 0
    for field_name, prov in provenance.items():
        w = weights.get(field_name, 0.5)
        total_w += w
        total_score += w * conf_map.get(prov["confidence"], 0.3)
    confidence_score = round(total_score / total_w, 2) if total_w > 0 else 0.3

    return MappingResult(
        scenario_input=input_dict,
        provenance=provenance,
        component_class=comp_class.value,
        warnings=warnings,
        confidence_score=confidence_score,
    )


def compute_product_impact(
    product: PMFProduct,
    target_component: str,
    modified_input: ScenarioInput,
    data: "LoadedData",
) -> dict:
    """Compute product-level impact of modifying a single component's scenario.

    Maps all components to baselines, calculates footprints, then replaces
    the target component's result with the user's modified scenario.
    """
    from .calculator import calculate_footprint

    component_baselines: dict[str, float] = {}
    target_baseline_co2e = 0.0
    target_found = False

    for comp in product.components.values():
        mapping = map_pmf_component(product, comp)
        try:
            baseline_input = ScenarioInput(**mapping.scenario_input)
            bd = calculate_footprint(baseline_input, data)
            component_baselines[comp.component] = bd.total
        except Exception:
            component_baselines[comp.component] = 0.0

        if comp.component == target_component:
            target_baseline_co2e = component_baselines[comp.component]
            target_found = True

    product_baseline_total = sum(component_baselines.values())

    # Calculate the modified component's footprint
    modified_bd = calculate_footprint(modified_input, data)
    modified_co2e = modified_bd.total

    component_delta = modified_co2e - target_baseline_co2e
    product_modified_total = product_baseline_total + component_delta

    target_comp = product.components.get(target_component)
    comp_mass = target_comp.total_mass_shipped_g if target_comp else 0
    mass_share = (comp_mass / product.total_mass_shipped_g * 100) if product.total_mass_shipped_g > 0 else 0

    return {
        "component_name": target_component,
        "component_baseline_co2e": round(target_baseline_co2e, 6),
        "component_modified_co2e": round(modified_co2e, 6),
        "component_delta_co2e": round(component_delta, 6),
        "component_delta_pct": round(
            (component_delta / target_baseline_co2e * 100) if target_baseline_co2e > 0 else 0, 2
        ),
        "product_name": product.name,
        "product_program": product.program,
        "product_total_mass_g": round(product.total_mass_shipped_g, 2),
        "product_component_count": len(product.components),
        "product_estimated_baseline_co2e": round(product_baseline_total, 6),
        "product_estimated_modified_co2e": round(product_modified_total, 6),
        "product_delta_co2e": round(component_delta, 6),
        "product_delta_pct": round(
            (component_delta / product_baseline_total * 100) if product_baseline_total > 0 else 0, 2
        ),
        "component_share_of_product_mass_pct": round(mass_share, 1),
        "is_estimated": True,
        "estimation_method": "component_delta_applied_to_product_baseline",
        "component_found": target_found,
    }


def generate_mapping_report(pmf_data: dict[str, PMFProduct]) -> dict:
    """Generate a full mapping audit report for all PMF products."""
    from datetime import datetime, timezone

    products_report = []
    all_warnings = []
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    material_coverage: dict[str, dict] = {}
    total_components = 0

    for prog, product in sorted(pmf_data.items()):
        comp_reports = []
        for comp in sorted(product.components.values(), key=lambda c: -c.total_mass_shipped_g):
            result = map_pmf_component(product, comp)
            total_components += 1

            # Count confidence
            mat_conf = result.provenance.get("material", {}).get("confidence", "low")
            confidence_counts[mat_conf] = confidence_counts.get(mat_conf, 0) + 1

            # Track material coverage
            cat = comp.dominant_material_category or "Unknown"
            if cat not in material_coverage:
                mapped_mat = result.provenance.get("material", {}).get("value", "N/A")
                mapped_conf = result.provenance.get("material", {}).get("confidence", "low")
                material_coverage[cat] = {
                    "count": 0, "model_material": mapped_mat, "confidence": mapped_conf,
                }
            material_coverage[cat]["count"] += 1

            rc_prov = result.provenance.get("recycled_content", {})

            comp_reports.append({
                "component": comp.component,
                "source_material_category": comp.dominant_material_category or "Unknown",
                "mapped_model_material": result.provenance.get("material", {}).get("value"),
                "source_recycled_content_pct": round(comp.recycled_content_pct, 1),
                "mapped_recycled_content_bucket": rc_prov.get("value", 0),
                "rc_snap_distance": round(abs(
                    comp.recycled_content_pct - rc_prov.get("value", 0)
                ), 1),
                "component_class": result.component_class,
                "confidence": result.confidence_score,
                "warnings": result.warnings,
                "mass_g": round(comp.total_mass_shipped_g, 2),
            })
            all_warnings.extend(result.warnings)

        products_report.append({
            "program": prog,
            "name": product.name,
            "product_group": product.product_group,
            "total_mass_g": round(product.total_mass_shipped_g, 2),
            "components": comp_reports,
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_products": len(pmf_data),
        "total_components": total_components,
        "mapping_summary": confidence_counts,
        "material_coverage": material_coverage,
        "warning_count": len(all_warnings),
        "unique_warnings": list(set(all_warnings)),
        "products": products_report,
    }
