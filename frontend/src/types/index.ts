export interface ScenarioInput {
  material: string;
  recycled_content: number;
  raw_material_blank_type: string;
  final_part_mass: number | null;
  final_part_volume: number | null;
  raw_material_mass: number;
  raw_material_volume: number | null;
  final_part_yield: number;
  plastic_injection_molding_parts_per_shot: number;
  plastic_injection_molding_cycle_time: number;
  forging_strikes: number;
  forging_trimming_bending_strikes: number;
  stamping_steps: number;
  heat_treatment_annealing_steps: number;
  heat_treatment_annealing_temperature: number;
  heat_treatment_tempering_steps: number;
  heat_treatment_tempering_temperature: number;
  laser_cutting_welding_cycle_time: number;
  laser_etching_cycle_time: number;
  sanding_cycle_time: number;
  machining_cycle_time: number;
  anodizing: boolean;
  electricity_grid: string;
}

export interface ProcessBreakdown {
  raw_material: number;
  upstream_processing: number;
  forging: number;
  stamping: number;
  heat_treatment: number;
  machining: number;
  laser: number;
  sanding: number;
  die_casting: number;
  injection_molding: number;
  anodizing: number;
  total: number;
}

export interface ProductContext {
  product_family: string | null;
  component_type: string | null;
  preset_id: string | null;
  part_name: string | null;
}

export interface PresetSummary {
  id: string;
  display_name: string;
  product_family: string;
  component_type: string;
  description: string;
}

export interface PresetDetail extends PresetSummary {
  parameters: ScenarioInput;
  adjustable_params: string[];
  locked_params: string[];
  allowed_materials: string[];
  allowed_blank_types: string[];
}

export interface ProductFamilyOption {
  value: string;
  component_types: string[];
}

export interface MaterialOption {
  value: string;
  valid_recycled_content: number[];
  carbon_intensities: Record<number, number>;
}

export interface GridOption {
  value: string;
  intensity: number;
}

export interface ScenarioSummary {
  id: string;
  name: string;
  total: number;
  material: string;
  recycled_content: number;
  created_at: string;
  product_family: string | null;
  component_type: string | null;
  part_name: string | null;
  origin: string;
}

export interface SavedScenario {
  id: string;
  name: string;
  input: ScenarioInput;
  breakdown: ProcessBreakdown;
  product_context: ProductContext | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  origin: string;
}

export interface FieldProvenance {
  value: unknown;
  source: string;   // "pmf_imported" | "pmf_inferred" | "class_default" | "model_default" | "user_edited"
  confidence: string; // "high" | "medium" | "low"
  notes: string;
}

export interface MappingResult {
  scenario_input: ScenarioInput;
  provenance: Record<string, FieldProvenance>;
  component_class: string;
  warnings: string[];
  confidence_score: number;
  product_name: string;
  product_group: string;
  model_validity?: ModelValidity;
}

export interface ModelValidity {
  status: "validated" | "approximate" | "unsupported";
  calculator: string;
  message: string;
}

export interface ParameterDiff {
  parameter: string;
  before: string | number | boolean | null;
  after: string | number | boolean | null;
  impact_direction: string;
}

export interface OptimizationResult {
  baseline_breakdown: ProcessBreakdown;
  optimized_input: ScenarioInput;
  optimized_breakdown: ProcessBreakdown;
  total_reduction_kg: number;
  total_reduction_pct: number;
  parameter_diffs: ParameterDiff[];
  constraints_applied: string[];
}

export const DEFAULT_INPUT: ScenarioInput = {
  material: "Alloy-F",
  recycled_content: 0,
  raw_material_blank_type: "Extruded",
  final_part_mass: null,
  final_part_volume: null,
  raw_material_mass: 1000,
  raw_material_volume: null,
  final_part_yield: 0.9,
  plastic_injection_molding_parts_per_shot: 0,
  plastic_injection_molding_cycle_time: 0,
  forging_strikes: 0,
  forging_trimming_bending_strikes: 0,
  stamping_steps: 0,
  heat_treatment_annealing_steps: 0,
  heat_treatment_annealing_temperature: 0,
  heat_treatment_tempering_steps: 0,
  heat_treatment_tempering_temperature: 0,
  laser_cutting_welding_cycle_time: 0,
  laser_etching_cycle_time: 0,
  sanding_cycle_time: 0,
  machining_cycle_time: 0,
  anodizing: false,
  electricity_grid: "Region A",
};

export const DEFAULT_PRODUCT_CONTEXT: ProductContext = {
  product_family: null,
  component_type: null,
  preset_id: null,
  part_name: null,
};

export const PROCESS_COLORS: Record<string, string> = {
  raw_material: "#4682B4",
  upstream_processing: "#87CEEB",
  forging: "#E67E22",
  stamping: "#F1C40F",
  heat_treatment: "#DC143C",
  machining: "#708090",
  laser: "#8E44AD",
  sanding: "#D2B48C",
  die_casting: "#D35400",
  injection_molding: "#27AE60",
  anodizing: "#008B8B",
};

export const PROCESS_LABELS: Record<string, string> = {
  raw_material: "Raw Material",
  upstream_processing: "Upstream Processing",
  forging: "Forging",
  stamping: "Stamping",
  heat_treatment: "Heat Treatment",
  machining: "Machining",
  laser: "Laser",
  sanding: "Sanding",
  die_casting: "Die Casting",
  injection_molding: "Injection Molding",
  anodizing: "Anodizing",
};
