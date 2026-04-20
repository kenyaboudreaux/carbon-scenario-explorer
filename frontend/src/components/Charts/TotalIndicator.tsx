import type { ProcessBreakdown } from "../../types";
import "./Charts.css";

interface Props {
  breakdown: ProcessBreakdown | null;
  loading: boolean;
  productLabel?: string;
}

export default function TotalIndicator({ breakdown, loading, productLabel }: Props) {
  if (!breakdown) return <div className="total-indicator">--</div>;

  const total = breakdown.total;
  const color = total < 1 ? "#27ae60" : total < 5 ? "#f39c12" : "#e74c3c";

  return (
    <div className="total-indicator" style={{ borderColor: color }}>
      <div className="total-label">
        {productLabel
          ? `Carbon Footprint for ${productLabel}`
          : "Total Carbon Footprint"}
      </div>
      <div className="total-value" style={{ color }}>
        {loading ? "..." : total.toFixed(4)}
      </div>
      <div className="total-unit">kg CO2e / unit</div>
    </div>
  );
}
