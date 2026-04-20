import axios from "axios";
import type {
  ScenarioInput,
  ProcessBreakdown,
  MaterialOption,
  GridOption,
  ScenarioSummary,
  SavedScenario,
  ProductFamilyOption,
  PresetSummary,
  PresetDetail,
  ProductContext,
  OptimizationResult,
  MappingResult,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

export async function calculate(input: ScenarioInput): Promise<ProcessBreakdown> {
  const { data } = await api.post<ProcessBreakdown>("/calculate", input);
  return data;
}

export async function getMaterials(): Promise<MaterialOption[]> {
  const { data } = await api.get<MaterialOption[]>("/reference/materials");
  return data;
}

export async function getGridOptions(): Promise<GridOption[]> {
  const { data } = await api.get<GridOption[]>("/reference/grid-options");
  return data;
}

export async function getBlankTypes(): Promise<{ value: string }[]> {
  const { data } = await api.get<{ value: string }[]>("/reference/blank-types");
  return data;
}

export async function getProductFamilies(): Promise<ProductFamilyOption[]> {
  const { data } = await api.get<ProductFamilyOption[]>("/reference/product-families");
  return data;
}

export async function getPresets(): Promise<PresetSummary[]> {
  const { data } = await api.get<PresetSummary[]>("/reference/presets");
  return data;
}

export async function getPreset(id: string): Promise<PresetDetail> {
  const { data } = await api.get<PresetDetail>(`/reference/presets/${id}`);
  return data;
}

export async function listScenarios(): Promise<ScenarioSummary[]> {
  const { data } = await api.get<ScenarioSummary[]>("/scenarios");
  return data;
}

export async function createScenario(
  name: string,
  input: ScenarioInput,
  productContext?: ProductContext | null,
  origin?: string,
  notes?: string
): Promise<SavedScenario> {
  const { data } = await api.post<SavedScenario>("/scenarios", {
    name,
    input,
    product_context: productContext || null,
    origin: origin || "manual",
    notes,
  });
  return data;
}

export async function getScenario(id: string): Promise<SavedScenario> {
  const { data } = await api.get<SavedScenario>(`/scenarios/${id}`);
  return data;
}

export async function deleteScenario(id: string): Promise<void> {
  await api.delete(`/scenarios/${id}`);
}

export async function compareScenarios(ids: string[]): Promise<SavedScenario[]> {
  const { data } = await api.post<SavedScenario[]>("/scenarios/compare", { ids });
  return data;
}

export async function exportCsv(ids: string[]): Promise<Blob> {
  const { data } = await api.post("/export/csv", { ids }, { responseType: "blob" });
  return data;
}

export async function exportDiffCsv(baselineId: string, comparisonIds: string[]): Promise<Blob> {
  const { data } = await api.post(
    "/export/diff-csv",
    { baseline_id: baselineId, comparison_ids: comparisonIds },
    { responseType: "blob" }
  );
  return data;
}

export async function optimize(
  input: ScenarioInput,
  presetId?: string | null
): Promise<OptimizationResult> {
  const { data } = await api.post<OptimizationResult>("/optimize", {
    input,
    preset_id: presetId || null,
  });
  return data;
}

// PMF (Product Material Footprint) endpoints
export interface PMFProductSummary {
  program: string;
  name: string;
  product_group: string;
  total_mass_g: number;
  recycled_content_pct: number;
  component_count: number;
  is_common_parts: boolean;
}

export interface PMFComponentDetail {
  component: string;
  subcomponents: string[];
  total_mass_shipped_g: number;
  recycled_content_pct: number;
  dominant_material_category: string;
  material_breakdown: Record<string, number>;
}

export interface PMFProductDetail {
  program: string;
  name: string;
  product_group: string;
  total_mass_shipped_g: number;
  recycled_content_pct: number;
  is_common_parts: boolean;
  component_count: number;
  components: PMFComponentDetail[];
}

export async function getPMFProducts(): Promise<PMFProductSummary[]> {
  const { data } = await api.get<PMFProductSummary[]>("/pmf/products");
  return data;
}

export async function getPMFProduct(program: string): Promise<PMFProductDetail> {
  const { data } = await api.get<PMFProductDetail>(`/pmf/products/${program}`);
  return data;
}

export async function getPMFGroups(): Promise<Record<string, PMFProductSummary[]>> {
  const { data } = await api.get<Record<string, PMFProductSummary[]>>("/pmf/groups");
  return data;
}

export async function mapPMFComponent(
  program: string,
  component: string
): Promise<MappingResult> {
  const { data } = await api.post<MappingResult>("/pmf/map-component", {
    program,
    component,
  });
  return data;
}

// Packaging calculator endpoints

export interface PackagingMaterial {
  name: string;
  gwp_kg_co2e_per_kg: number;
}

export async function getPackagingMaterials(): Promise<PackagingMaterial[]> {
  const { data } = await api.get<PackagingMaterial[]>("/packaging/materials");
  return data;
}

export async function calculatePackaging(params: {
  raw_material_mass: number;
  packaging_material: string;
  yield_pct: number;
  efficiency_pct: number;
  air_pct: number;
  sea_pct: number;
  ground_pct: number;
}): Promise<ProcessBreakdown> {
  const { data } = await api.post<ProcessBreakdown>("/packaging/calculate", params);
  return data;
}
