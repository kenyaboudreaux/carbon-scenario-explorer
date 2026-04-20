from typing import Optional
from pydantic import BaseModel, Field, model_validator

from .enums import Material, BlankType, ElectricityGrid, VALID_RECYCLED_CONTENT, ALL_RECYCLED_CONTENT


class ScenarioInput(BaseModel):
    material: Material
    recycled_content: int = Field(default=0, description="Recycled content percentage (0, 25, 30, 50, 75, 100)")
    raw_material_blank_type: BlankType
    final_part_mass: Optional[float] = Field(default=None, ge=0, description="grams")
    final_part_volume: Optional[float] = Field(default=None, ge=0, description="mm3")
    raw_material_mass: float = Field(gt=0, description="grams")
    raw_material_volume: Optional[float] = Field(default=None, ge=0, description="mm3")
    final_part_yield: float = Field(default=0.90, ge=0, le=1)
    plastic_injection_molding_parts_per_shot: int = Field(default=0, ge=0)
    plastic_injection_molding_cycle_time: float = Field(default=0, ge=0, description="sec/shot")
    forging_strikes: int = Field(default=0, ge=0)
    forging_trimming_bending_strikes: int = Field(default=0, ge=0)
    stamping_steps: int = Field(default=0, ge=0)
    heat_treatment_annealing_steps: int = Field(default=0, ge=0)
    heat_treatment_annealing_temperature: float = Field(default=0, ge=0, description="Celsius")
    heat_treatment_tempering_steps: int = Field(default=0, ge=0)
    heat_treatment_tempering_temperature: float = Field(default=0, ge=0, description="Celsius")
    laser_cutting_welding_cycle_time: float = Field(default=0, ge=0, description="sec/pc")
    laser_etching_cycle_time: float = Field(default=0, ge=0, description="sec/pc")
    sanding_cycle_time: float = Field(default=0, ge=0, description="sec/pc")
    machining_cycle_time: float = Field(default=0, ge=0, description="sec/pc")
    anodizing: bool = False
    electricity_grid: ElectricityGrid = ElectricityGrid.REGION_A

    @model_validator(mode="after")
    def validate_recycled_content(self):
        valid = VALID_RECYCLED_CONTENT.get(self.material, ALL_RECYCLED_CONTENT)
        if self.recycled_content not in valid:
            raise ValueError(
                f"Material {self.material.value} supports recycled content: {valid}. "
                f"Got {self.recycled_content}."
            )
        return self


class ProcessBreakdown(BaseModel):
    raw_material: float = 0.0
    upstream_processing: float = 0.0
    forging: float = 0.0
    stamping: float = 0.0
    heat_treatment: float = 0.0
    machining: float = 0.0
    laser: float = 0.0
    sanding: float = 0.0
    die_casting: float = 0.0
    injection_molding: float = 0.0
    anodizing: float = 0.0
    total: float = 0.0
    model_version: str = ""
    data_version: str = ""
    assumptions_hash: str = ""


class ProductContext(BaseModel):
    product_family: Optional[str] = None
    component_type: Optional[str] = None
    preset_id: Optional[str] = None
    part_name: Optional[str] = None


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    input: ScenarioInput
    product_context: Optional[ProductContext] = None
    notes: Optional[str] = None
    origin: str = "manual"


class ScenarioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    notes: Optional[str] = None


class SavedScenario(BaseModel):
    id: str
    name: str
    input: ScenarioInput
    breakdown: ProcessBreakdown
    product_context: Optional[ProductContext] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    model_version: str = "unknown"
    data_version: str = "unknown"
    assumptions_hash: str = "unknown"
    origin: str = "manual"


class ScenarioSummary(BaseModel):
    id: str
    name: str
    total: float
    material: str
    recycled_content: int
    created_at: str
    product_family: Optional[str] = None
    component_type: Optional[str] = None
    part_name: Optional[str] = None
    origin: str = "manual"


class ParameterDiff(BaseModel):
    parameter: str
    before: str | float | bool | None
    after: str | float | bool | None
    impact_direction: str = ""


class OptimizationResult(BaseModel):
    baseline_breakdown: ProcessBreakdown
    optimized_input: ScenarioInput
    optimized_breakdown: ProcessBreakdown
    total_reduction_kg: float
    total_reduction_pct: float
    parameter_diffs: list[ParameterDiff]
    constraints_applied: list[str]


class FormulaStep(BaseModel):
    process: str
    formula: str
    inputs: dict
    intermediate: dict
    result: float
    unit: str = "kg CO2e"


class FormulaTrace(BaseModel):
    steps: list[FormulaStep]
    breakdown: ProcessBreakdown
    constants_used: dict
    grid_intensity: float
    mass_kg: float
