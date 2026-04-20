import { useState, useEffect, useCallback } from "react";
import type { ScenarioSummary, ScenarioInput, SavedScenario, ProductContext } from "../types";
import {
  listScenarios,
  createScenario,
  deleteScenario as apiDelete,
  getScenario,
  compareScenarios as apiCompare,
  exportCsv,
} from "../api/client";

export function useScenarios() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<SavedScenario[]>([]);

  const refresh = useCallback(async () => {
    try {
      const list = await listScenarios();
      setScenarios(list);
    } catch {
      /* backend may not be up yet */
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const save = async (
    name: string,
    input: ScenarioInput,
    productContext?: ProductContext | null,
    origin?: string,
    notes?: string
  ) => {
    await createScenario(name, input, productContext, origin, notes);
    await refresh();
  };

  const remove = async (id: string) => {
    await apiDelete(id);
    setSelectedIds((prev) => prev.filter((i) => i !== id));
    await refresh();
  };

  const load = async (id: string): Promise<SavedScenario> => {
    return getScenario(id);
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const compare = async () => {
    if (selectedIds.length < 2) return;
    const data = await apiCompare(selectedIds);
    setComparisonData(data);
  };

  const downloadCsv = async () => {
    const ids = selectedIds.length > 0 ? selectedIds : scenarios.map((s) => s.id);
    const blob = await exportCsv(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scenarios_export.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return {
    scenarios,
    selectedIds,
    comparisonData,
    save,
    remove,
    load,
    toggleSelect,
    compare,
    downloadCsv,
    refresh,
  };
}
