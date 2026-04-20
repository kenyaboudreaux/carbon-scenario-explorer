import { useState } from "react";
import "./Info.css";

export default function ModelInfoPanel() {
  const [open, setOpen] = useState(false);

  return (
    <div className="info-panel">
      <button className="info-toggle" onClick={() => setOpen(!open)}>
        {open ? "Hide" : "Show"} Model Information
      </button>
      {open && (
        <div className="info-content">
          <div className="info-section">
            <h4>About this tool</h4>
            <p>Carbon Scenario Explorer uses anonymized, public-safe sample data to demonstrate product and component scenario modeling. Adjust manufacturing parameters and see how changes affect carbon footprint outcomes.</p>
          </div>
          <div className="info-section">
            <h4>Current modeling scope</h4>
            <p>The system includes two validated calculators: a <strong>mass-based metal/polymer manufacturing model</strong> for enclosure-style components, and a <strong>packaging calculator</strong> with material GWP and shipping modal split. Components in other categories show validity badges indicating approximate or unsupported status.</p>
          </div>
          <div className="info-section">
            <h4>Validated calculators</h4>
            <ul>
              <li><strong>Enclosure / manufacturing</strong> -- 11 process formulas for metal and polymer parts</li>
              <li><strong>Packaging</strong> -- material GWP lookup + shipping carbon by modal split (air / sea / ground)</li>
            </ul>
          </div>
          <div className="info-section">
            <h4>Categories not yet supported</h4>
            <ul>
              <li><strong>Electronics</strong> -- requires area-based calculator</li>
              <li><strong>Textiles / soft goods</strong> -- requires fiber supply-chain model</li>
              <li><strong>Logistics / transportation</strong> -- requires route-based model</li>
              <li><strong>Specialty metals</strong> -- requires alloy-specific profiles</li>
            </ul>
          </div>
          <div className="info-section">
            <h4>What the model covers</h4>
            <p>11 process formulas: raw material production, upstream semi-fabrication (extrusion, rolling, die casting), forging, stamping, heat treatment, machining, laser cutting/etching, sanding, injection molding, and anodizing.</p>
          </div>
          <div className="info-section">
            <h4>Optimization (Beta)</h4>
            <p>The optimizer evaluates grid switching, recycled content maximization, material substitution, and blank type changes within the mass-based calculator. It is fully functional for validated categories, directional for approximate categories, and disabled for unsupported categories.</p>
          </div>
          <div className="info-section">
            <h4>Confidence levels</h4>
            <ul>
              <li><span className="conf-dot conf-high" /> <strong>High</strong> -- directly from source data</li>
              <li><span className="conf-dot conf-medium" /> <strong>Medium</strong> -- inferred from component class or category</li>
              <li><span className="conf-dot conf-low" /> <strong>Low</strong> -- model defaults with no supporting data</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
