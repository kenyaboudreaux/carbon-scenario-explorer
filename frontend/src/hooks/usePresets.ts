import { useState, useEffect, useCallback } from "react";
import type { ProductFamilyOption, PresetSummary, PresetDetail } from "../types";
import { getProductFamilies, getPresets, getPreset } from "../api/client";

export function usePresets() {
  const [families, setFamilies] = useState<ProductFamilyOption[]>([]);
  const [presets, setPresets] = useState<PresetSummary[]>([]);
  const [activePreset, setActivePreset] = useState<PresetDetail | null>(null);

  useEffect(() => {
    Promise.all([getProductFamilies(), getPresets()])
      .then(([f, p]) => {
        setFamilies(f);
        setPresets(p);
      })
      .catch(() => {});
  }, []);

  const loadPreset = useCallback(async (presetId: string) => {
    const detail = await getPreset(presetId);
    setActivePreset(detail);
    return detail;
  }, []);

  const clearPreset = useCallback(() => {
    setActivePreset(null);
  }, []);

  const presetsForFamily = useCallback(
    (family: string | null) => {
      if (!family) return presets;
      return presets.filter((p) => p.product_family === family);
    },
    [presets]
  );

  return { families, presets, activePreset, loadPreset, clearPreset, presetsForFamily };
}
