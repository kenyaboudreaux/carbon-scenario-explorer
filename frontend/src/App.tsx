import { useState, useCallback } from "react";
import Layout from "./components/Layout/Layout";
import ProductSelector from "./components/Controls/ProductSelector";
import ScenarioForm from "./components/Controls/ScenarioForm";
import TotalIndicator from "./components/Charts/TotalIndicator";
import ProductImpactSummary from "./components/Charts/ProductImpactSummary";
import BreakdownBarChart from "./components/Charts/BreakdownBarChart";
import WaterfallChart from "./components/Charts/WaterfallChart";
import ScenarioManager from "./components/Scenarios/ScenarioManager";
import ComparisonView from "./components/Scenarios/ComparisonView";
import OptimizeButton from "./components/Optimize/OptimizeButton";
import ModelInfoPanel from "./components/Info/ModelInfoPanel";
import LandingView from "./components/Landing/LandingView";
import ScenarioReport from "./components/Report/ScenarioReport";
import { useCalculation } from "./hooks/useCalculation";
import { useReferenceData } from "./hooks/useReferenceData";
import { useScenarios } from "./hooks/useScenarios";
import { usePresets } from "./hooks/usePresets";
import type { ScenarioInput, ProductContext, FieldProvenance, ModelValidity } from "./types";
import { DEFAULT_INPUT, DEFAULT_PRODUCT_CONTEXT } from "./types";
import { mapPMFComponent } from "./api/client";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState<"model" | "compare" | "report">("model");
  const [input, setInput] = useState<ScenarioInput>(DEFAULT_INPUT);
  const [productContext, setProductContext] = useState<ProductContext>(DEFAULT_PRODUCT_CONTEXT);
  const [baselineInput, setBaselineInput] = useState<ScenarioInput | null>(null);
  const [lockedParams, setLockedParams] = useState<string[]>([]);
  const [provenance, setProvenance] = useState<Record<string, FieldProvenance> | null>(null);
  const [mappingWarnings, setMappingWarnings] = useState<string[]>([]);
  const [pmfProgram, setPmfProgram] = useState<string | null>(null);
  const [pmfComponent, setPmfComponent] = useState<string | null>(null);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [modelValidity, setModelValidity] = useState<ModelValidity | null>(null);

  const { breakdown, loading, error } = useCalculation(input);
  const { materials, gridOptions, blankTypes, loaded } = useReferenceData();
  const { families, activePreset, loadPreset, clearPreset, presetsForFamily } = usePresets();
  const {
    scenarios, selectedIds, save, remove, load, toggleSelect, downloadCsv,
  } = useScenarios();

  const productLabel =
    productContext.part_name ||
    (activePreset ? activePreset.display_name : null) ||
    (productContext.product_family && productContext.component_type
      ? `${productContext.product_family} ${productContext.component_type}`
      : "");

  const showLanding = activeTab === "model" && !hasInteracted && !productContext.product_family && !productContext.preset_id;

  const handlePresetSelect = useCallback(
    async (presetId: string) => {
      const detail = await loadPreset(presetId);
      const params = detail.parameters as ScenarioInput;
      setInput(params);
      setBaselineInput(params);
      setLockedParams(detail.locked_params || []);
      setProductContext({
        product_family: detail.product_family,
        component_type: detail.component_type,
        preset_id: detail.id,
        part_name: productContext.part_name,
      });
      setHasInteracted(true);
    },
    [loadPreset, productContext.part_name]
  );

  const handleFamilyChange = useCallback(
    (family: string | null) => {
      setProductContext((prev) => ({
        ...prev,
        product_family: family,
        component_type: null,
        preset_id: null,
      }));
      if (family) setHasInteracted(true);
      if (!family) {
        clearPreset();
        setBaselineInput(null);
        setLockedParams([]);
      }
    },
    [clearPreset]
  );

  const handleClearProduct = useCallback(() => {
    setProductContext(DEFAULT_PRODUCT_CONTEXT);
    setInput(DEFAULT_INPUT);
    setBaselineInput(null);
    setLockedParams([]);
    setProvenance(null);
    setMappingWarnings([]);
    setPmfProgram(null);
    setPmfComponent(null);
    setHasInteracted(false);
    setModelValidity(null);
    clearPreset();
  }, [clearPreset]);

  const handlePMFComponentSelect = useCallback(
    async (program: string, component: string, _massG: number, _rcPct: number, productName: string) => {
      setHasInteracted(true);
      try {
        const result = await mapPMFComponent(program, component);
        const mappedInput = result.scenario_input as ScenarioInput;
        setInput(mappedInput);
        setProvenance(result.provenance as Record<string, FieldProvenance>);
        setMappingWarnings(result.warnings);
        setModelValidity((result as { model_validity?: ModelValidity }).model_validity || null);
        setPmfProgram(program);
        setPmfComponent(component);
        setProductContext({
          product_family: result.product_group,
          component_type: component,
          preset_id: null,
          part_name: `${productName} — ${component}`,
        });
        setBaselineInput(mappedInput);
        setLockedParams(["raw_material_mass"]);
      } catch {
        const updatedInput: ScenarioInput = { ...DEFAULT_INPUT, raw_material_mass: Math.max(_massG, 1) };
        setInput(updatedInput);
        setProvenance(null);
        setMappingWarnings(["Backend mapping failed; using default parameters"]);
        setProductContext({ product_family: null, component_type: component, preset_id: null, part_name: `${productName} — ${component}` });
        setBaselineInput(updatedInput);
        setLockedParams(["raw_material_mass"]);
      }
    },
    []
  );

  const handleDemoSelect = useCallback(
    async (demo: { program: string; component: string; modifications: Record<string, unknown> }) => {
      setHasInteracted(true);
      setActiveTab("model");
      try {
        const result = await mapPMFComponent(demo.program, demo.component);
        const mappedInput = { ...(result.scenario_input as ScenarioInput), ...demo.modifications } as ScenarioInput;
        setInput(mappedInput);
        setProvenance(result.provenance as Record<string, FieldProvenance>);
        setMappingWarnings(result.warnings);
        setPmfProgram(demo.program);
        setPmfComponent(demo.component);
        setProductContext({
          product_family: result.product_group,
          component_type: demo.component,
          preset_id: null,
          part_name: `${result.product_name} — ${demo.component}`,
        });
        setBaselineInput(result.scenario_input as ScenarioInput);
        setLockedParams(["raw_material_mass"]);
      } catch { /* landing fallback */ }
    },
    []
  );

  const handleLoad = useCallback(
    async (id: string) => {
      const s = await load(id);
      setInput(s.input);
      setHasInteracted(true);
      if (s.product_context) {
        setProductContext(s.product_context);
        if (s.product_context.preset_id) {
          try {
            const detail = await loadPreset(s.product_context.preset_id);
            setBaselineInput(detail.parameters as ScenarioInput);
            setLockedParams(detail.locked_params || []);
          } catch { setBaselineInput(null); setLockedParams([]); }
        }
      }
      setActiveTab("model");
    },
    [load, loadPreset]
  );

  const handleReset = useCallback(() => {
    if (baselineInput) {
      setInput(baselineInput);
    } else {
      setInput(DEFAULT_INPUT);
      setProductContext(DEFAULT_PRODUCT_CONTEXT);
      setLockedParams([]);
      setHasInteracted(false);
      clearPreset();
    }
  }, [baselineInput, clearPreset]);

  const handleSave = useCallback(
    async (name: string, _input: ScenarioInput, notes?: string) => {
      await save(name, _input, productContext, "manual", notes);
    },
    [save, productContext]
  );

  const handleOptimizeSave = useCallback(
    async (name: string, optimizedInput: ScenarioInput, origin: string) => {
      await save(name, optimizedInput, productContext, origin);
    },
    [save, productContext]
  );

  if (!loaded) {
    return (
      <div className="loading">
        <p>Loading reference data...</p>
        <p className="loading-hint">Make sure the backend is running on port 8000</p>
      </div>
    );
  }

  const sidebar = (
    <ScenarioManager
      scenarios={scenarios}
      selectedIds={selectedIds}
      currentInput={input}
      productContext={productContext}
      onSave={handleSave}
      onDelete={remove}
      onLoad={handleLoad}
      onToggleSelect={toggleSelect}
      onReset={handleReset}
      onExport={downloadCsv}
    />
  );

  return (
    <Layout
      sidebar={sidebar}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      modelingLabel={productLabel || undefined}
    >
      {activeTab === "model" && showLanding ? (
        <div className="landing-container">
          <LandingView
            onStartProduct={() => { setHasInteracted(true); }}
            onStartBlank={() => { setHasInteracted(true); }}
            onDemoSelect={handleDemoSelect}
          />
        </div>
      ) : activeTab === "model" ? (
        <div className="model-view">
          <div className="controls-panel">
            <ProductSelector
              productContext={productContext}
              families={families}
              presets={presetsForFamily(productContext.product_family)}
              presetsForFamily={presetsForFamily}
              activePresetName={activePreset?.display_name ?? null}
              onFamilyChange={handleFamilyChange}
              onPresetSelect={handlePresetSelect}
              onPartNameChange={(name) =>
                setProductContext((prev) => ({ ...prev, part_name: name || null }))
              }
              onClear={handleClearProduct}
              onPMFComponentSelect={handlePMFComponentSelect}
            />
            <ScenarioForm
              input={input}
              onChange={setInput}
              materials={materials}
              gridOptions={gridOptions}
              blankTypes={blankTypes}
              lockedParams={lockedParams}
              baselineInput={baselineInput}
              provenance={provenance}
            />
          </div>
          <div className="charts-panel">
            {modelValidity && (
              <div className={`validity-banner validity-${modelValidity.status}`}>
                <span className={`validity-badge validity-badge-${modelValidity.status}`}>
                  {modelValidity.status === "validated" ? "Validated" : modelValidity.status === "approximate" ? "Approximate" : "Unsupported"}
                </span>
                <span className="validity-message">{modelValidity.message}</span>
              </div>
            )}
            {mappingWarnings.length > 0 && (
              <div className="warning-banner">
                <strong>Mapping Warnings:</strong>
                <ul>
                  {mappingWarnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}
            {error && <div className="error-banner">{error}</div>}
            <TotalIndicator
              breakdown={breakdown}
              loading={loading}
              productLabel={productLabel || undefined}
            />
            <ProductImpactSummary
              program={pmfProgram}
              component={pmfComponent}
              input={input}
            />
            <BreakdownBarChart breakdown={breakdown} />
            <WaterfallChart breakdown={breakdown} />
            <OptimizeButton
              input={input}
              presetId={productContext.preset_id}
              productLabel={productLabel}
              onApply={(optimizedInput) => setInput(optimizedInput)}
              onSave={handleOptimizeSave}
              modelValidity={modelValidity}
            />
            <ModelInfoPanel />
          </div>
        </div>
      ) : activeTab === "compare" ? (
        <div className="compare-view">
          <ComparisonView selectedIds={selectedIds} />
        </div>
      ) : (
        <div className="report-view">
          <ScenarioReport
            input={input}
            breakdown={breakdown}
            productContext={productContext}
            provenance={provenance}
            mappingWarnings={mappingWarnings}
            productLabel={productLabel}
            modelValidity={modelValidity}
          />
        </div>
      )}
    </Layout>
  );
}

export default App;
