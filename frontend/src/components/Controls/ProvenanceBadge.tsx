import "./Controls.css";

interface Props {
  source: string;
  confidence: string;
  notes?: string;
}

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  pmf_imported: { label: "PMF", color: "#27ae60" },
  pmf_inferred: { label: "Inferred", color: "#f39c12" },
  class_default: { label: "Class default", color: "#f39c12" },
  model_default: { label: "Default", color: "#95a5a6" },
  user_edited: { label: "Edited", color: "#2d6cdf" },
};

const CONF_COLORS: Record<string, string> = {
  high: "#27ae60",
  medium: "#f39c12",
  low: "#95a5a6",
};

export default function ProvenanceBadge({ source, confidence, notes }: Props) {
  const info = SOURCE_LABELS[source] || { label: source, color: "#95a5a6" };
  const dotColor = CONF_COLORS[confidence] || "#95a5a6";

  return (
    <span className="provenance-badge" title={notes || `${info.label} (${confidence} confidence)`}>
      <span className="prov-dot" style={{ backgroundColor: dotColor }} />
      <span className="prov-label" style={{ color: info.color }}>{info.label}</span>
    </span>
  );
}
