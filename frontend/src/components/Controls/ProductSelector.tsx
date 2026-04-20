import { useState, useEffect } from "react";
import type { ProductContext, ProductFamilyOption, PresetSummary } from "../../types";
import { getPMFProducts, getPMFProduct, type PMFProductSummary, type PMFProductDetail } from "../../api/client";
import "./Controls.css";

interface Props {
  productContext: ProductContext;
  families: ProductFamilyOption[];
  presets: PresetSummary[];
  presetsForFamily: (family: string | null) => PresetSummary[];
  activePresetName: string | null;
  onFamilyChange: (family: string | null) => void;
  onPresetSelect: (presetId: string) => void;
  onPartNameChange: (name: string) => void;
  onClear: () => void;
  onPMFComponentSelect: (program: string, component: string, massG: number, rcPct: number, productName: string) => void;
}

export default function ProductSelector({
  productContext,
  families,
  presetsForFamily,
  activePresetName,
  onFamilyChange,
  onPresetSelect,
  onPartNameChange,
  onClear,
  onPMFComponentSelect,
}: Props) {
  const [pmfProducts, setPmfProducts] = useState<PMFProductSummary[]>([]);
  const [pmfDetail, setPmfDetail] = useState<PMFProductDetail | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<string>("");
  const [pmfLoaded, setPmfLoaded] = useState(false);

  useEffect(() => {
    getPMFProducts()
      .then((p) => { setPmfProducts(p); setPmfLoaded(true); })
      .catch(() => setPmfLoaded(true));
  }, []);

  const matchingPresets = presetsForFamily(productContext.product_family);
  const familyOption = families.find((f) => f.value === productContext.product_family);
  const componentTypes = familyOption?.component_types ?? [];

  // Filter PMF products by selected family
  const pmfForFamily = productContext.product_family
    ? pmfProducts.filter((p) => p.product_group === productContext.product_family)
    : pmfProducts;

  const handleProgramSelect = async (program: string) => {
    setSelectedProgram(program);
    if (program) {
      try {
        const detail = await getPMFProduct(program);
        setPmfDetail(detail);
      } catch {
        setPmfDetail(null);
      }
    } else {
      setPmfDetail(null);
    }
  };

  const handleComponentClick = (comp: PMFProductDetail["components"][0]) => {
    if (!pmfDetail) return;
    onPMFComponentSelect(
      pmfDetail.program,
      comp.component,
      comp.total_mass_shipped_g,
      comp.recycled_content_pct,
      pmfDetail.name,
    );
  };

  return (
    <div className="product-selector">
      <div className="ps-header">
        <h3>Product Context</h3>
        {(productContext.preset_id || selectedProgram) && (
          <button className="btn-small btn-outline" onClick={() => {
            onClear();
            setSelectedProgram("");
            setPmfDetail(null);
          }}>
            Clear
          </button>
        )}
      </div>

      {activePresetName && (
        <div className="ps-baseline-banner">
          Editing from baseline: <strong>{activePresetName}</strong>
        </div>
      )}

      <div className="ps-fields">
        <div className="field">
          <label>Product Family</label>
          <select
            value={productContext.product_family ?? ""}
            onChange={(e) => {
              onFamilyChange(e.target.value || null);
              setSelectedProgram("");
              setPmfDetail(null);
            }}
          >
            <option value="">No product context</option>
            {families.map((f) => (
              <option key={f.value} value={f.value}>{f.value}</option>
            ))}
          </select>
        </div>

        {productContext.product_family && componentTypes.length > 0 && (
          <div className="field">
            <label>Component Type</label>
            <select
              value={productContext.component_type ?? ""}
              onChange={() => {}}
              disabled
            >
              <option value="">
                {productContext.component_type || "Select a preset or PMF product"}
              </option>
              {componentTypes.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        )}

        {matchingPresets.length > 0 && (
          <div className="field">
            <label>Baseline Preset</label>
            <select
              value={productContext.preset_id ?? ""}
              onChange={(e) => {
                if (e.target.value) onPresetSelect(e.target.value);
              }}
            >
              <option value="">Select a baseline...</option>
              {matchingPresets.map((p) => (
                <option key={p.id} value={p.id}>{p.display_name}</option>
              ))}
            </select>
          </div>
        )}

        {pmfLoaded && pmfForFamily.length > 0 && (
          <div className="field">
            <label>PMF Product Data ({pmfForFamily.length} products)</label>
            <select
              value={selectedProgram}
              onChange={(e) => handleProgramSelect(e.target.value)}
            >
              <option value="">Browse real product BOM data...</option>
              {pmfForFamily.map((p) => (
                <option key={p.program} value={p.program}>
                  {p.name} ({p.program}) — {p.total_mass_g.toFixed(0)}g, {p.recycled_content_pct}% RC
                </option>
              ))}
            </select>
          </div>
        )}

        {pmfDetail && (
          <div className="pmf-components">
            <label className="pmf-comp-label">
              {pmfDetail.name} — Components ({pmfDetail.component_count})
            </label>
            <div className="pmf-comp-list">
              {pmfDetail.components.slice(0, 12).map((comp) => (
                <button
                  key={comp.component}
                  className="pmf-comp-item"
                  onClick={() => handleComponentClick(comp)}
                  title={`Click to use ${comp.total_mass_shipped_g.toFixed(1)}g as raw material mass`}
                >
                  <span className="pmf-comp-name">{comp.component}</span>
                  <span className="pmf-comp-mass">{comp.total_mass_shipped_g.toFixed(1)}g</span>
                  <span className="pmf-comp-rc">{comp.recycled_content_pct}% RC</span>
                  <span className="pmf-comp-mat">{comp.dominant_material_category}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="field">
          <label>Part Name</label>
          <input
            type="text"
            className="sm-name-input"
            placeholder="e.g. Smartphone housing"
            value={productContext.part_name ?? ""}
            onChange={(e) => onPartNameChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
