import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ProcessBreakdown } from "../../types";
import { PROCESS_COLORS, PROCESS_LABELS } from "../../types";

interface Props {
  breakdown: ProcessBreakdown | null;
}

const PROCESS_KEYS = [
  "raw_material",
  "upstream_processing",
  "forging",
  "stamping",
  "heat_treatment",
  "machining",
  "laser",
  "sanding",
  "die_casting",
  "injection_molding",
  "anodizing",
] as const;

export default function BreakdownBarChart({ breakdown }: Props) {
  if (!breakdown) return null;

  const data = PROCESS_KEYS.filter(
    (k) => breakdown[k] > 0.00001
  ).map((key) => ({
    name: PROCESS_LABELS[key],
    value: breakdown[key],
    color: PROCESS_COLORS[key],
  }));

  if (data.length === 0) {
    return <div className="chart-empty">No emissions to display</div>;
  }

  return (
    <div className="chart-container">
      <h3 className="chart-title">Process Breakdown</h3>
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 40 + 70)}>
        <BarChart data={data} layout="vertical" margin={{ left: 120, right: 30, top: 5, bottom: 24 }}>
          <XAxis type="number" tick={{ fontSize: 11 }} label={{ value: "kg CO2e/unit", position: "insideBottom", offset: -12, fontSize: 11, fill: "#888" }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
          <Tooltip
            formatter={(value: number) => [value.toFixed(6) + " kg CO2e", "Impact"]}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="value" name="kg CO2e" radius={[0, 4, 4, 0]}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
