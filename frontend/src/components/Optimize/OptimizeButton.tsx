import { useState } from "react";
import type { ScenarioInput, OptimizationResult, ModelValidity } from "../../types";
import { optimize } from "../../api/client";
import OptimizeResultView from "./OptimizeResultView";
import "./Optimize.css";

interface Props {
  input: ScenarioInput;
  presetId: string | null;
  productLabel: string;
  onApply: (input: ScenarioInput) => void;
  onSave: (name: string, input: ScenarioInput, origin: string) => void;
  modelValidity: ModelValidity | null;
}

export default function OptimizeButton({ input, presetId, productLabel, onApply, onSave, modelValidity }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await optimize(input, presetId);
      setResult(r);
    } catch {
      setError("Optimization failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const status = modelValidity?.status ?? "validated";

  return (
    <div className="optimize-section">
      {status === "unsupported" ? (
        <div className="optimize-disabled">
          <span className="validity-badge validity-badge-unsupported">Unsupported</span>
          <span>Optimization is not available for this component type. A category-specific calculator has not been implemented.</span>
        </div>
      ) : (
        <>
          {status === "approximate" && (
            <div className="optimize-warning">
              The optimizer is running on an approximate mass-based model. Adjustments are applied using the current generic calculator and may not reflect category-specific behavior.
            </div>
          )}
          <button className="optimize-btn" onClick={handleOptimize} disabled={loading}>
            {loading ? "Optimizing..." : "Optimize Scenario (Beta)"}
          </button>
        </>
      )}

      {error && <div className="opt-error">{error}</div>}

      {result && (
        <OptimizeResultView
          result={result}
          productLabel={productLabel}
          modelValidityStatus={status}
          onApply={() => {
            onApply(result.optimized_input);
            setResult(null);
          }}
          onSave={() => {
            const name = productLabel
              ? `${productLabel} - Optimized`
              : "Optimized Scenario";
            onSave(name, result.optimized_input, "optimized");
            setResult(null);
          }}
          onDismiss={() => setResult(null)}
        />
      )}
    </div>
  );
}
