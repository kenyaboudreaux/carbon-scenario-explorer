import type { ReactNode } from "react";
import "./Layout.css";

interface Props {
  sidebar: ReactNode;
  children: ReactNode;
  activeTab: "model" | "compare" | "report";
  onTabChange: (tab: "model" | "compare" | "report") => void;
  modelingLabel?: string;
}

export default function Layout({
  sidebar, children, activeTab, onTabChange, modelingLabel,
}: Props) {
  const subtitle = modelingLabel
    ? `Modeling: ${modelingLabel}`
    : "Product-aware scenario analysis with anonymized sample data";

  return (
    <div className="layout">
      <header className="header">
        <h1 className="header-title">Carbon Scenario Explorer</h1>
        <p className="header-sub">{subtitle}</p>
        <nav className="tabs">
          <button
            className={`tab ${activeTab === "model" ? "active" : ""}`}
            onClick={() => onTabChange("model")}
          >
            Interactive Modeling
          </button>
          <button
            className={`tab ${activeTab === "compare" ? "active" : ""}`}
            onClick={() => onTabChange("compare")}
          >
            Scenario Comparison
          </button>
          <button
            className={`tab ${activeTab === "report" ? "active" : ""}`}
            onClick={() => onTabChange("report")}
          >
            Scenario Report
          </button>
        </nav>
      </header>
      <div className="scope-note">
        Validated calculators: mass-based metal/polymer manufacturing and packaging (material GWP + shipping). Electronics, textiles, and logistics require category-specific calculators not yet implemented.
      </div>
      <div className="main">
        <aside className="sidebar">{sidebar}</aside>
        <section className="content">{children}</section>
      </div>
    </div>
  );
}
