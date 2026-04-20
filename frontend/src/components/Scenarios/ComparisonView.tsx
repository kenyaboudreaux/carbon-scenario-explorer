import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { SavedScenario } from "../../types";
import { PROCESS_COLORS, PROCESS_LABELS } from "../../types";
import { compareScenarios } from "../../api/client";

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

interface Props {
  selectedIds: string[];
}

export default function ComparisonView({ selectedIds }: Props) {
  const [scenarios, setScenarios] = useState<SavedScenario[]>([]);

  useEffect(() => {
    if (selectedIds.length < 2) {
      setScenarios([]);
      return;
    }
    compareScenarios(selectedIds).then(setScenarios).catch(() => {});
  }, [selectedIds]);

  if (selectedIds.length < 2) {
    return (
      <div className="comparison-empty">
        <h3>Compare baseline, modified, and optimized scenarios side by side</h3>
        <p>Select 2 or more saved scenarios to compare them.</p>
        <p style={{ fontSize: 12, color: "#aaa" }}>
          Use the checkboxes in the sidebar to select scenarios.
        </p>
      </div>
    );
  }

  if (scenarios.length === 0) return null;

  // Build stacked bar chart data: one group per scenario, stacked by process
  const chartData = scenarios.map((s) => {
    const entry: Record<string, string | number> = { name: s.name };
    for (const key of PROCESS_KEYS) {
      entry[key] = s.breakdown[key];
    }
    entry.total = s.breakdown.total;
    return entry;
  });

  // Active process keys (at least one scenario has > 0)
  const activeKeys = PROCESS_KEYS.filter((k) =>
    scenarios.some((s) => s.breakdown[k] > 0.00001)
  );

  return (
    <div className="comparison-view">
      <h3 className="chart-title" style={{ marginBottom: 16 }}>Scenario Comparison</h3>

      <div className="chart-container" style={{ marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ left: 20, right: 30, top: 5, bottom: 5 }}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis
              tick={{ fontSize: 11 }}
              label={{
                value: "kg CO2e/unit",
                angle: -90,
                position: "insideLeft",
                fontSize: 11,
              }}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                value.toFixed(6) + " kg CO2e",
                PROCESS_LABELS[name] || name,
              ]}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend formatter={(v: string) => PROCESS_LABELS[v] || v} />
            {activeKeys.map((key) => (
              <Bar
                key={key}
                dataKey={key}
                stackId="a"
                fill={PROCESS_COLORS[key]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="comparison-table-wrapper">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Parameter</th>
              {scenarios.map((s) => (
                <th key={s.id}>{s.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Material</td>
              {scenarios.map((s) => <td key={s.id}>{s.input.material}</td>)}
            </tr>
            <tr>
              <td>Recycled Content</td>
              {scenarios.map((s) => <td key={s.id}>{s.input.recycled_content}%</td>)}
            </tr>
            <tr>
              <td>Blank Type</td>
              {scenarios.map((s) => <td key={s.id}>{s.input.raw_material_blank_type}</td>)}
            </tr>
            <tr>
              <td>Raw Material Mass</td>
              {scenarios.map((s) => <td key={s.id}>{s.input.raw_material_mass} g</td>)}
            </tr>
            <tr>
              <td>Grid</td>
              {scenarios.map((s) => <td key={s.id}>{s.input.electricity_grid}</td>)}
            </tr>
            <tr className="table-divider"><td colSpan={scenarios.length + 1}>Results</td></tr>
            {PROCESS_KEYS.map((key) => (
              <tr key={key}>
                <td>{PROCESS_LABELS[key]}</td>
                {scenarios.map((s) => (
                  <td key={s.id}>{s.breakdown[key].toFixed(6)}</td>
                ))}
              </tr>
            ))}
            <tr className="total-row">
              <td>Total</td>
              {scenarios.map((s) => (
                <td key={s.id}>{s.breakdown.total.toFixed(6)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
