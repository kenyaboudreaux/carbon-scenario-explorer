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

export default function WaterfallChart({ breakdown }: Props) {
  if (!breakdown) return null;

  const activeProcesses = PROCESS_KEYS.filter((k) => breakdown[k] > 0.00001);
  if (activeProcesses.length === 0) return null;

  let cumulative = 0;
  const data = activeProcesses.map((key) => {
    const base = cumulative;
    const val = breakdown[key];
    cumulative += val;
    return {
      name: PROCESS_LABELS[key],
      base: base,
      value: val,
      cumulative: cumulative,
      color: PROCESS_COLORS[key],
    };
  });

  // Add total bar
  data.push({
    name: "Total",
    base: 0,
    value: cumulative,
    cumulative: cumulative,
    color: "#1a1a2e",
  });

  return (
    <div className="chart-container">
      <h3 className="chart-title">Cumulative Emissions (Waterfall)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ left: 120, right: 30, top: 5, bottom: 24 }} layout="vertical">
          <XAxis type="number" tick={{ fontSize: 11 }} label={{ value: "kg CO2e/unit", position: "insideBottom", offset: -12, fontSize: 11, fill: "#888" }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === "base") return [null, null];
              return [value.toFixed(6) + " kg CO2e", "Impact"];
            }}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="base" stackId="a" fill="transparent" />
          <Bar dataKey="value" stackId="a" radius={[0, 4, 4, 0]}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
