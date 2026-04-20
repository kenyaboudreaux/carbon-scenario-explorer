import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import type { OptimizationResult } from "../../types";
import { PROCESS_COLORS, PROCESS_LABELS } from "../../types";
import "./Optimize.css";

const PROCESS_KEYS = [
  "raw_material", "upstream_processing", "forging", "stamping",
  "heat_treatment", "machining", "laser", "sanding",
  "die_casting", "injection_molding", "anodizing",
] as const;

interface Props {
  result: OptimizationResult;
  productLabel: string;
  modelValidityStatus: string;
  onApply: () => void;
  onSave: () => void;
  onDismiss: () => void;
}

export default function OptimizeResultView({ result, productLabel, modelValidityStatus, onApply, onSave, onDismiss }: Props) {
  const { baseline_breakdown: base, optimized_breakdown: opt, parameter_diffs: diffs } = result;

  const chartData = [
    { name: "Baseline", ...Object.fromEntries(PROCESS_KEYS.map((k) => [k, base[k]])) },
    { name: "Optimized", ...Object.fromEntries(PROCESS_KEYS.map((k) => [k, opt[k]])) },
  ];

  const activeKeys = PROCESS_KEYS.filter((k) => base[k] > 0.00001 || opt[k] > 0.00001);

  return (
    <div className="opt-result">
      <div className="opt-result-header">
        <h3>Optimization Result {productLabel && <span>for {productLabel}</span>}</h3>
        <button className="btn-small btn-outline" onClick={onDismiss}>Dismiss</button>
      </div>

      {modelValidityStatus === "approximate" && (
        <div className="opt-validity-note opt-validity-approximate">
          These results are approximate. The optimizer used the mass-based calculator, which may not fully represent this component category.
        </div>
      )}

      <div className="opt-summary">
        <div className="opt-card">
          <div className="opt-card-label">Baseline</div>
          <div className="opt-card-value">{base.total.toFixed(4)}</div>
          <div className="opt-card-unit">kg CO2e</div>
        </div>
        <div className="opt-arrow">-&gt;</div>
        <div className="opt-card optimized">
          <div className="opt-card-label">Optimized</div>
          <div className="opt-card-value">{opt.total.toFixed(4)}</div>
          <div className="opt-card-unit">kg CO2e</div>
        </div>
        <div className="opt-card reduction">
          <div className="opt-card-label">Reduction</div>
          <div className="opt-card-value">-{result.total_reduction_pct}%</div>
          <div className="opt-card-unit">(-{result.total_reduction_kg.toFixed(4)} kg)</div>
        </div>
      </div>

      {diffs.length > 0 && (
        <div className="opt-diffs">
          <h4>Parameter Changes</h4>
          <table className="opt-diff-table">
            <thead>
              <tr><th>Parameter</th><th>Before</th><th>After</th><th>Direction</th></tr>
            </thead>
            <tbody>
              {diffs.map((d) => (
                <tr key={d.parameter}>
                  <td>{d.parameter.replace(/_/g, " ")}</td>
                  <td>{String(d.before)}</td>
                  <td className="opt-after">{String(d.after)}</td>
                  <td className="opt-lower">{d.impact_direction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="opt-chart">
        <h4>Breakdown Comparison</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ left: 20, right: 20 }}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: number, name: string) => [
                value.toFixed(6), PROCESS_LABELS[name] || name,
              ]}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend formatter={(v: string) => PROCESS_LABELS[v] || v} />
            {activeKeys.map((key) => (
              <Bar key={key} dataKey={key} stackId="a" fill={PROCESS_COLORS[key]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="opt-constraints">
        <h4>Methodology</h4>
        {modelValidityStatus === "validated" ? (
          <p className="opt-methodology">The optimizer evaluated grid switching, recycled content maximization, material substitution, and blank type changes within the validated mass-based calculator.</p>
        ) : (
          <p className="opt-methodology">The optimizer evaluated parameter changes using the generic mass-based calculator. Results should be interpreted as directional guidance, not precise category-specific recommendations.</p>
        )}
        <h4>Constraints Applied</h4>
        <ul>
          {result.constraints_applied.map((c, i) => <li key={i}>{c}</li>)}
        </ul>
      </div>

      <div className="opt-actions">
        <button className="btn-small btn-primary" onClick={onApply}>
          Apply Optimized Parameters
        </button>
        <button className="btn-small btn-outline" onClick={onSave}>
          Save as Scenario
        </button>
      </div>
    </div>
  );
}
