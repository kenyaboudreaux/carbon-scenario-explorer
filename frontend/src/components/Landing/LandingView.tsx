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
  onViewMethodology?: () => void;
  onCompareScenarios?: () => void;
}

const GROUP_COLORS: Record<string, string> = {
  Phone: "#0a84ff",
  Laptop: "#8e8e93",
  Tablet: "#5e5ce6",
  Wearable: "#30b0a0",
};

// What a user can change (inputs) and what the system returns (outputs).
const CHANGE_CARDS: { title: string; desc: string }[] = [
  { title: "Material swaps", desc: "Compare alloys and polymers by carbon intensity." },
  { title: "Recycled content", desc: "Raise recycled fraction and see the delta." },
  { title: "Vendor / source", desc: "Model source assumptions via material & grid." },
  { title: "Manufacturing grid", desc: "Switch region or 100% renewable electricity." },
  { title: "Process mix", desc: "Adjust machining, forming, and finishing steps." },
  { title: "Packaging materials", desc: "Trade higher- for lower-GWP packaging." },
  { title: "Shipping modal split", desc: "Shift between air, sea, and ground." },
  { title: "Component mass", desc: "Test lightweighting against footprint." },
  { title: "Product rollup", desc: "See a component change at product scale." },
];

const RETURN_CARDS: { title: string; desc: string }[] = [
  { title: "Estimated carbon impact", desc: "Scenario footprint in kg CO2e." },
  { title: "Baseline vs. scenario delta", desc: "Absolute and percent change." },
  { title: "Process breakdown", desc: "Contribution of each process step." },
  { title: "Component contribution", desc: "How one part sits in the product." },
  { title: "Product-level rollup", desc: "Component delta applied to product." },
  { title: "Provenance & confidence", desc: "Source type and confidence per field." },
  { title: "Model validity badge", desc: "Validated, approximate, or unsupported." },
  { title: "Formula / audit trace", desc: "Expand to see formulas and values." },
];

export default function LandingView({
  onStartProduct,
  onStartBlank,
  onDemoSelect,
  onViewMethodology,
  onCompareScenarios,
}: Props) {
  const [demos, setDemos] = useState<DemoScenario[]>([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL || "/api"}/reference/demo-scenarios`)
      .then((r) => r.json())
      .then(setDemos)
      .catch(() => {});
  }, []);

  return (
    <div className="landing">
      {/* 1. Hero */}
      <div className="landing-hero">
        <div className="landing-eyebrow">Public demo · synthetic / external data only</div>
        <h2>Carbon Scenario Explorer</h2>
        <p className="landing-subtitle">
          Real-time carbon scenario modeling for product development decisions.
        </p>
        <p className="landing-lede">
          Explore how material choices, recycled content, vendor/source assumptions,
          manufacturing processes, packaging decisions, and logistics parameters affect
          estimated product carbon intensity — before those decisions become locked into a
          product plan.
        </p>
        <div className="landing-cta">
          <button className="cta-btn cta-primary" onClick={onStartProduct}>
            Open Demo
          </button>
          {onViewMethodology && (
            <button className="cta-btn" onClick={onViewMethodology}>
              View Methodology
            </button>
          )}
          {onCompareScenarios && (
            <button className="cta-btn" onClick={onCompareScenarios}>
              Compare Scenarios
            </button>
          )}
        </div>
      </div>

      {/* Start options */}
      <div className="landing-actions">
        <button className="landing-card primary" onClick={onStartProduct}>
          <div className="lc-icon">P</div>
          <div className="lc-text">
            <div className="lc-title">Start with a product</div>
            <div className="lc-desc">
              Browse demo products and components with BOM-style mass and material data.
            </div>
          </div>
        </button>
        <button className="landing-card" onClick={onStartBlank}>
          <div className="lc-icon">+</div>
          <div className="lc-text">
            <div className="lc-title">Start from scratch</div>
            <div className="lc-desc">
              Begin with a blank scenario and configure parameters directly.
            </div>
          </div>
        </button>
      </div>

      {/* Suggested guided scenarios */}
      {demos.length > 0 && (
        <div className="landing-demos">
          <h3>Guided scenarios</h3>
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

      {/* 2. Why it matters */}
      <div className="landing-section">
        <h3>Why it matters</h3>
        <p className="section-copy">
          Most carbon impact is shaped upstream, when product teams choose materials,
          suppliers, manufacturing methods, packaging formats, and logistics assumptions.
          Carbon Scenario Explorer turns those choices into live scenario comparisons so
          teams can see impact while decisions are still actionable.
        </p>
        <p className="section-audience">
          Built for product development engineers, engineering managers, hardware program
          teams, environmental product analysts, operations/manufacturing teams,
          sustainability reviewers, and technical leaders evaluating tradeoffs.
        </p>
      </div>

      {/* 3. What users can change */}
      <div className="landing-section">
        <h3>What you can change</h3>
        <div className="feature-grid">
          {CHANGE_CARDS.map((c) => (
            <div key={c.title} className="feature-card">
              <div className="feature-title">{c.title}</div>
              <div className="feature-desc">{c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. What the system returns */}
      <div className="landing-section">
        <h3>What you get back</h3>
        <div className="feature-grid">
          {RETURN_CARDS.map((c) => (
            <div key={c.title} className="feature-card">
              <div className="feature-title">{c.title}</div>
              <div className="feature-desc">{c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Model validity system */}
      <div className="landing-section validity-section">
        <h3>Model validity — no false precision</h3>
        <p className="section-copy">
          The tool does not silently produce false precision. Each component is labeled with
          a model-validity status so users can distinguish validated calculator coverage from
          approximate or unsupported categories.
        </p>
        <div className="validity-rows">
          <div className="validity-row">
            <span className="validity-chip validity-chip-validated">Validated</span>
            <span>Category-specific calculator with domain-appropriate methodology.</span>
          </div>
          <div className="validity-row">
            <span className="validity-chip validity-chip-approximate">Approximate</span>
            <span>Generic mass-based estimate; treat as directional.</span>
          </div>
          <div className="validity-row">
            <span className="validity-chip validity-chip-unsupported">Unsupported</span>
            <span>Not modeled — no misleading result is shown.</span>
          </div>
        </div>
      </div>

      {/* 6. Public demo safety */}
      <div className="landing-section safety-section">
        <h3>Public demo safety</h3>
        <p className="section-copy">
          This public deployment uses synthetic and external demo-safe data. It demonstrates
          the system architecture and user workflow without exposing confidential PMF
          records or proprietary product data. The architecture supports separated internal
          and external data adapters; this deployment runs in public demo mode.
        </p>
      </div>

      <div className="landing-footer">
        This tool provides scenario estimates for exploratory engineering analysis. It is not
        a certified LCA, regulatory carbon accounting report, or official product
        environmental report. Dataset content is anonymized and illustrative.
      </div>
    </div>
  );
}
