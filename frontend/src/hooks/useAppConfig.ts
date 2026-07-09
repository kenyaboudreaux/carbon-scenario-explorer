import { useState, useEffect } from "react";
import { getConfig, type AppConfig } from "../api/client";

/**
 * Fetches public runtime config (data mode / version) from the backend.
 * Falls back to a safe "public demo" default if the API is unreachable so the
 * demo badge and disclaimers always render.
 */
export function useAppConfig(): AppConfig | null {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    let active = true;
    getConfig()
      .then((c) => {
        if (active) setConfig(c);
      })
      .catch(() => {
        if (active)
          setConfig({
            public_demo_mode: true,
            data_mode: "external",
            dataset_label: "Public demo dataset — synthetic / external data only",
            model_version: "",
            data_version: "",
          });
      });
    return () => {
      active = false;
    };
  }, []);

  return config;
}
