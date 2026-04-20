import { useState, useEffect } from "react";
import type { MaterialOption, GridOption } from "../types";
import { getMaterials, getGridOptions, getBlankTypes } from "../api/client";

export function useReferenceData() {
  const [materials, setMaterials] = useState<MaterialOption[]>([]);
  const [gridOptions, setGridOptions] = useState<GridOption[]>([]);
  const [blankTypes, setBlankTypes] = useState<{ value: string }[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([getMaterials(), getGridOptions(), getBlankTypes()])
      .then(([m, g, b]) => {
        setMaterials(m);
        setGridOptions(g);
        setBlankTypes(b);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  return { materials, gridOptions, blankTypes, loaded };
}
