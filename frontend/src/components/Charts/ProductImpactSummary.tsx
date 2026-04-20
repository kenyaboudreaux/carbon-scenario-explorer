import { useState, useEffect } from "react";
import type { ScenarioInput } from "../../types";
import "./Charts.css";

interface ProductImpact {
  component_name: string;
  component_baseline_co2e: number;
  component_modified_co2e: number;
  component_delta_co2e: number;
  component_delta_pct: number;
  product_name: string;
  product_estimated_baseline_co2e: number;
  product_estimated_modified_co2e: number;
  product_delta_co2e: number;
  product_delta_pct: number;
  component_share_of_product_mass_pct: number;
  is_estimated: boolean;
}

interface Props {
  program: string | null;
  component: string | null;
  input: ScenarioInput;
}

export default function ProductImpactSummary({ program, component, input }: Props) {
  const [impact, setImpact] = useState<ProductImpact | null>(null);

  useEffect(() => {
    if (!program || !component) {
      setImpact(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"}/pmf/product-impact`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ program, component, scenario_input: input }),
        });
        if (res.ok) setImpact(await res.json());
      } catch { /* ignore */ }
    }, 300);
    return () => clearTimeout(timer);
  }, [program, component, input]);

  if (!impact) return null;

  const compUp = impact.component_delta_co2e > 0;
  const prodUp = impact.product_delta_co2e > 0;

  return (
    <div className="product-impact">
      <div className="pi-header">
        <h4>Product Impact Summary</h4>
        <span className="pi-estimated" title="Calculated by applying component delta to estimated product baseline">
          Estimated
        </span>
      </div>

      <div className="pi-grid">
        <div className="pi-section">
          <div className="pi-section-label">Component: {impact.component_name}</div>
          <div className="pi-row">
            <span>Baseline</span>
            <span>{impact.component_baseline_co2e.toFixed(4)} kg</span>
          </div>
          <div className="pi-row">
            <span>Modified</span>
            <span>{impact.component_modified_co2e.toFixed(4)} kg</span>
          </div>
          <div className={`pi-row pi-delta ${compUp ? "up" : "down"}`}>
            <span>Delta</span>
            <span>
              {compUp ? "+" : ""}{impact.component_delta_co2e.toFixed(4)} kg ({compUp ? "+" : ""}{impact.component_delta_pct.toFixed(1)}%)
            </span>
          </div>
        </div>

        <div className="pi-section">
          <div className="pi-section-label">Product: {impact.product_name}</div>
          <div className="pi-row">
            <span>Baseline (est.)</span>
            <span>{impact.product_estimated_baseline_co2e.toFixed(4)} kg</span>
          </div>
          <div className="pi-row">
            <span>Modified (est.)</span>
            <span>{impact.product_estimated_modified_co2e.toFixed(4)} kg</span>
          </div>
          <div className={`pi-row pi-delta ${prodUp ? "up" : "down"}`}>
            <span>Delta</span>
            <span>
              {prodUp ? "+" : ""}{impact.product_delta_co2e.toFixed(4)} kg ({prodUp ? "+" : ""}{impact.product_delta_pct.toFixed(1)}%)
            </span>
          </div>
          <div className="pi-row pi-share">
            <span>Component mass share</span>
            <span>{impact.component_share_of_product_mass_pct}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
