"""Load and aggregate PMF (Product Material Footprint) data from CSV files.

PMF files provide actual BOM material composition data for consumer electronics products.
This data feeds the product selector with real mass/material values.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..config import DATA_DIR, require_public_safe_dataset

logger = logging.getLogger(__name__)

PMF_DIR = DATA_DIR / "pmf"

# Standard columns present in all PMF variants
BASE_COLS = [
    "program", "proxyProject", "proxyConfig", "name", "component",
    "subcomponent", "materialCategory", "materialName", "substanceGroup",
    "substanceName", "productGroup", "productLine", "status",
]

# Product code → product group mapping (fallback when productGroup column is empty)
CODE_PREFIX_MAP = {
    "SP": "Phone",
    
    
    "TB": "Tablet", "LP": "Laptop", "WR": "Wearable",
}


@dataclass
class PMFProduct:
    """Aggregated PMF data for one product."""
    program: str
    name: str
    product_group: str
    components: dict[str, "PMFComponent"] = field(default_factory=dict)
    total_mass_shipped_g: float = 0.0
    total_mass_mobilized_g: float = 0.0
    recycled_content_pct: float = 0.0
    is_common_parts: bool = False


@dataclass
class PMFComponent:
    """Aggregated material data for one component within a product."""
    component: str
    subcomponents: list[str] = field(default_factory=list)
    total_mass_shipped_g: float = 0.0
    total_mass_mobilized_g: float = 0.0
    recycled_mass_shipped_g: float = 0.0
    primary_mass_shipped_g: float = 0.0
    recycled_content_pct: float = 0.0
    material_breakdown: dict[str, float] = field(default_factory=dict)
    dominant_material_category: str = ""
    dominant_material_name: str = ""


def _infer_product_group(program: str) -> str:
    for prefix, group in CODE_PREFIX_MAP.items():
        if program.startswith(prefix):
            return group
    return "Unknown"


def load_pmf_data() -> dict[str, PMFProduct]:
    """Load all PMF CSV files and return aggregated product data."""
    if not PMF_DIR.exists():
        logger.warning(f"PMF directory not found: {PMF_DIR}")
        return {}

    # Guardrail: in public/external mode, only demo-safe bundled data is allowed.
    require_public_safe_dataset(PMF_DIR)

    products: dict[str, PMFProduct] = {}

    for csv_file in sorted(PMF_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(csv_file, low_memory=False)
        except Exception as e:
            logger.warning(f"Failed to read {csv_file.name}: {e}")
            continue

        if df.empty or "program" not in df.columns:
            continue

        # Filter to shipped rows only
        if "status" in df.columns:
            df_shipped = df[df["status"] == "shipped"]
            if df_shipped.empty:
                df_shipped = df  # use all rows if none are "shipped"
        else:
            df_shipped = df

        is_common = "Common parts" in csv_file.name

        # Get unique programs in this file
        for program in df_shipped["program"].dropna().unique():
            prog_df = df_shipped[df_shipped["program"] == program]
            if prog_df.empty:
                continue

            # Product-level info
            name = prog_df["name"].dropna().iloc[0] if not prog_df["name"].dropna().empty else program
            pg = prog_df["productGroup"].dropna().iloc[0] if "productGroup" in prog_df.columns and not prog_df["productGroup"].dropna().empty else _infer_product_group(program)

            if program not in products:
                products[program] = PMFProduct(
                    program=program, name=str(name), product_group=str(pg),
                    is_common_parts=is_common,
                )
            product = products[program]

            # Aggregate by component
            for comp_name, comp_df in prog_df.groupby("component", dropna=False):
                comp_key = str(comp_name) if pd.notna(comp_name) else "Unknown"
                if comp_key not in product.components:
                    product.components[comp_key] = PMFComponent(component=comp_key)
                comp = product.components[comp_key]

                # Subcomponents
                if "subcomponent" in comp_df.columns:
                    subs = comp_df["subcomponent"].dropna().unique().tolist()
                    for s in subs:
                        if s and str(s) not in comp.subcomponents:
                            comp.subcomponents.append(str(s))

                # Mass aggregation (handle both schema variants)
                shipped_col = "materialMassShipped"
                mobilized_col = "materialMassMobilized"
                rc_shipped = "massShippedRcCert" if "massShippedRcCert" in comp_df.columns else None
                primary_shipped = "massShippedPrimary" if "massShippedPrimary" in comp_df.columns else None

                if shipped_col in comp_df.columns:
                    mass = pd.to_numeric(comp_df[shipped_col], errors="coerce").sum()
                    comp.total_mass_shipped_g += mass
                if mobilized_col in comp_df.columns:
                    mass = pd.to_numeric(comp_df[mobilized_col], errors="coerce").sum()
                    comp.total_mass_mobilized_g += mass
                if rc_shipped and rc_shipped in comp_df.columns:
                    rc_mass = pd.to_numeric(comp_df[rc_shipped], errors="coerce").sum()
                    comp.recycled_mass_shipped_g += rc_mass
                if primary_shipped and primary_shipped in comp_df.columns:
                    pr_mass = pd.to_numeric(comp_df[primary_shipped], errors="coerce").sum()
                    comp.primary_mass_shipped_g += pr_mass

                # Material category breakdown (aggregate shipped mass by category)
                if "materialCategory" in comp_df.columns and shipped_col in comp_df.columns:
                    for cat, cat_df in comp_df.groupby("materialCategory", dropna=False):
                        cat_str = str(cat) if pd.notna(cat) else "Unknown"
                        cat_mass = pd.to_numeric(cat_df[shipped_col], errors="coerce").sum()
                        comp.material_breakdown[cat_str] = comp.material_breakdown.get(cat_str, 0) + cat_mass

            # Finalize component-level stats
            for comp in product.components.values():
                total = comp.total_mass_shipped_g
                if total > 0:
                    comp.recycled_content_pct = round(
                        comp.recycled_mass_shipped_g / total * 100, 1
                    ) if total > 0 else 0.0

                # Dominant material
                if comp.material_breakdown:
                    dom = max(comp.material_breakdown.items(), key=lambda x: x[1])
                    comp.dominant_material_category = dom[0]

            # Product-level totals
            product.total_mass_shipped_g = sum(c.total_mass_shipped_g for c in product.components.values())
            product.total_mass_mobilized_g = sum(c.total_mass_mobilized_g for c in product.components.values())
            total_rc = sum(c.recycled_mass_shipped_g for c in product.components.values())
            if product.total_mass_shipped_g > 0:
                product.recycled_content_pct = round(total_rc / product.total_mass_shipped_g * 100, 1)

    # Sanity filter: drop products with unrealistic mass (> 100 kg)
    filtered = {k: v for k, v in products.items() if v.total_mass_shipped_g < 100_000}
    dropped = len(products) - len(filtered)
    if dropped:
        logger.warning(f"Dropped {dropped} products with unrealistic mass values")

    logger.info(f"Loaded PMF data: {len(filtered)} products, "
                f"{sum(len(p.components) for p in filtered.values())} components")
    return filtered


def pmf_product_to_dict(product: PMFProduct) -> dict:
    """Serialize a PMFProduct for API response."""
    return {
        "program": product.program,
        "name": product.name,
        "product_group": product.product_group,
        "total_mass_shipped_g": round(product.total_mass_shipped_g, 2),
        "recycled_content_pct": product.recycled_content_pct,
        "is_common_parts": product.is_common_parts,
        "component_count": len(product.components),
        "components": [
            {
                "component": c.component,
                "subcomponents": c.subcomponents,
                "total_mass_shipped_g": round(c.total_mass_shipped_g, 4),
                "recycled_content_pct": c.recycled_content_pct,
                "dominant_material_category": c.dominant_material_category,
                "material_breakdown": {
                    k: round(v, 4) for k, v in sorted(
                        c.material_breakdown.items(), key=lambda x: -x[1]
                    ) if v > 0.0001
                },
            }
            for c in sorted(product.components.values(), key=lambda x: -x.total_mass_shipped_g)
        ],
    }
