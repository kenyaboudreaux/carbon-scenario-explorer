import { useState, useEffect } from "react";
import "./Landing.css";

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  program: string;
  component: string;
  modifications: Record<string, unknown>;
  product_group: string;
  run_optimizer?: boolean;
}

interface Props {
  onStartProduct: () => void;
  onStartBlank: () => void;
  onDemoSelect: (demo: DemoScenario) => void;
}

const GROUP_COLORS: Record<string, string> = {
  Phone: "#007AFF",
  Laptop: "#A2AAAD",
  Tablet: "#5856D6",
  Wearable: "#FF3B30",
};

export default function LandingView({ onStartProduct, onStartBlank, onDemoSelect }: Props) {
  const [demos, setDemos] = useState<DemoScenario[]>([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"}/reference/demo-scenarios`)
      .then((r) => r.json())
      .then(setDemos)
      .catch(() => {});
  }, []);

  return (
    <div className="landing">
      <div className="landing-hero">
        <h2>Model scenarios. Compare alternatives. Understand impact.</h2>
        <p className="landing-subtitle">
          Carbon Scenario Explorer currently models mass-based metal and polymer manufacturing
          scenarios. Adjust parameters for anonymized product components and see how changes
          affect calculated outcomes in real time.
        </p>
      </div>

      <div className="landing-actions">
        <button className="landing-card primary" onClick={onStartProduct}>
          <div className="lc-icon">P</div>
          <div className="lc-text">
            <div className="lc-title">Start with a product</div>
            <div className="lc-desc">Browse sample products and components with real BOM-style mass and material data.</div>
          </div>
        </button>
        <button className="landing-card" onClick={onStartBlank}>
          <div className="lc-icon">+</div>
          <div className="lc-text">
            <div className="lc-title">Start from scratch</div>
            <div className="lc-desc">Begin with a blank scenario and configure all 24 parameters directly.</div>
          </div>
        </button>
      </div>

      {demos.length > 0 && (
        <div className="landing-demos">
          <h3>Suggested Scenarios</h3>
          <div className="demo-grid">
            {demos.map((d) => (
              <button key={d.id} className="demo-tile" onClick={() => onDemoSelect(d)}>
                <span
                  className="demo-badge"
                  style={{ background: GROUP_COLORS[d.product_group] || "#888" }}
                >
                  {d.product_group}
                </span>
                <div className="demo-title">{d.title}</div>
                <div className="demo-desc">{d.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="landing-about">
        <h3>What this tool does</h3>
        <ul>
          <li>Models carbon footprint across 11 mass-based manufacturing process formulas</li>
          <li>Validated for metal enclosures, polymer housings, and packaging components</li>
          <li>Uses anonymized sample data with field-level provenance and model validity indicators</li>
          <li>Compares baseline, modified, and optimized scenarios side by side</li>
          <li>Generates printable reports with full traceability</li>
        </ul>
        <p style={{fontSize: 11, color: "#888", marginTop: 8}}>
          Additional category-specific calculators (electronics, textiles, logistics) are planned but not yet implemented.
        </p>
      </div>

      <div className="landing-footer">
        Dataset content is anonymized and illustrative. This is a public-safe demonstration tool.
      </div>
    </div>
  );
}
