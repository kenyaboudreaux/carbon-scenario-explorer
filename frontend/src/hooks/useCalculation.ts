import { useState, useEffect, useRef, useCallback } from "react";
import type { ScenarioInput, ProcessBreakdown } from "../types";
import { calculate } from "../api/client";

export function useCalculation(input: ScenarioInput) {
  const [breakdown, setBreakdown] = useState<ProcessBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const recalculate = useCallback((currentInput: ScenarioInput) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await calculate(currentInput);
        setBreakdown(result);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Calculation failed";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }, 150);
  }, []);

  useEffect(() => {
    recalculate(input);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [input, recalculate]);

  return { breakdown, loading, error };
}
