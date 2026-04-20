import { useState } from "react";
import type { ScenarioInput, ScenarioSummary, ProductContext } from "../../types";
import "./Scenarios.css";

interface Props {
  scenarios: ScenarioSummary[];
  selectedIds: string[];
  currentInput: ScenarioInput;
  productContext: ProductContext;
  onSave: (name: string, input: ScenarioInput, notes?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onLoad: (id: string) => void;
  onToggleSelect: (id: string) => void;
  onReset: () => void;
  onExport: () => void;
}

export default function ScenarioManager({
  scenarios,
  selectedIds,
  currentInput,
  productContext,
  onSave,
  onDelete,
  onLoad,
  onToggleSelect,
  onReset,
  onExport,
}: Props) {
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    const defaultName = productContext.part_name || productContext.product_family
      ? `${productContext.product_family || ""} ${productContext.part_name || ""}`.trim()
      : "";
    await onSave(name.trim() || defaultName || "Untitled", currentInput);
    setName("");
    setSaving(false);
  };

  return (
    <div className="scenario-manager">
      <div className="sm-header">
        <h3>Scenarios</h3>
        <button className="btn-small btn-outline" onClick={onReset}>
          Reset
        </button>
      </div>

      <div className="sm-save">
        <input
          type="text"
          placeholder="Scenario name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSave()}
          className="sm-name-input"
        />
        <button className="btn-small btn-primary" onClick={handleSave} disabled={saving || !name.trim()}>
          Save
        </button>
      </div>

      <div className="sm-list">
        {scenarios.length === 0 && (
          <div className="sm-empty">No saved scenarios yet</div>
        )}
        {scenarios.map((s) => (
          <div key={s.id} className="scenario-card">
            <div className="sc-top">
              <input
                type="checkbox"
                checked={selectedIds.includes(s.id)}
                onChange={() => onToggleSelect(s.id)}
              />
              <div className="sc-info" onClick={() => onLoad(s.id)}>
                <div className="sc-name">
                  {s.product_family && <span className="sc-badge">[{s.product_family}]</span>}
                  {" "}{s.name}
                </div>
                <div className="sc-meta">
                  {s.material} | {s.recycled_content}% RC | {s.total.toFixed(4)} kg CO2e
                  {s.origin !== "manual" && (
                    <span className={`sc-origin sc-origin-${s.origin}`}>
                      {s.origin === "optimized" ? " Optimized" : s.origin === "preset" ? " Preset" : ""}
                    </span>
                  )}
                </div>
              </div>
              <button className="btn-delete" onClick={() => onDelete(s.id)}>
                x
              </button>
            </div>
          </div>
        ))}
      </div>

      {scenarios.length > 0 && (
        <button className="btn-small btn-outline sm-export" onClick={onExport}>
          Export CSV
        </button>
      )}
    </div>
  );
}
