import type { ReactNode } from "react";
import "./Layout.css";

interface Props {
  sidebar: ReactNode;
  children: ReactNode;
  activeTab: "model" | "compare" | "report";
  onTabChange: (tab: "model" | "compare" | "report") => void;
  modelingLabel?: string;
  datasetLabel?: string;
  dataMode?: string;
}

export default function Layout({
  sidebar, children, activeTab, onTabChange, modelingLabel, datasetLabel, dataMode,
}: Props) {
  const subtitle = modelingLabel
    ? `Modeling: ${modelingLabel}`
    : "Real-time carbon scenario modeling for product development decisions";

  const badgeLabel = datasetLabel || "Public demo dataset — synthetic / external data only";

  return (
    <div className="layout">
      <header className="header">
        <div className="header-topline">
          <h1 className="header-title">Carbon Scenario Explorer</h1>
          <span className="demo-badge-pill" title={badgeLabel}>
            <span className="demo-badge-dot" />
            Public demo{dataMode ? ` · ${dataMode} data` : ""}
          </span>
        </div>
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
