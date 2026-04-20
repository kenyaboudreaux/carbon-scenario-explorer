import { useState, useCallback } from "react";
import type {
  ScenarioInput,
  MaterialOption,
  GridOption,
  FieldProvenance,
} from "../../types";
import ProvenanceBadge from "./ProvenanceBadge";
import "./Controls.css";

interface Props {
  input: ScenarioInput;
  onChange: (input: ScenarioInput) => void;
  materials: MaterialOption[];
  gridOptions: GridOption[];
  blankTypes: { value: string }[];
  lockedParams?: string[];
  baselineInput?: ScenarioInput | null;
  provenance?: Record<string, FieldProvenance> | null;
}

function ParameterGroup({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="param-group">
      <button className="param-group-header" onClick={() => setOpen(!open)}>
        <span>{title}</span>
        <span className="chevron">{open ? "\u25B2" : "\u25BC"}</span>
      </button>
      {open && <div className="param-group-body">{children}</div>}
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="field">
      <div className="field-header">
        <label>{label}</label>
        <div className="field-value">
          <input
            type="number"
            value={value}
            min={min}
            max={max}
            step={step}
            onChange={(e) => onChange(Number(e.target.value))}
            className="num-input"
          />
          {unit && <span className="unit">{unit}</span>}
        </div>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="slider"
      />
    </div>
  );
}

export default function ScenarioForm({
  input,
  onChange,
  materials,
  gridOptions,
  blankTypes,
  lockedParams = [],
  baselineInput,
  provenance,
}: Props) {
  const locked = new Set(lockedParams);
  const isLocked = (name: string) => locked.has(name);
  const isModified = (name: string) => {
    if (!baselineInput) return false;
    const bv = (baselineInput as Record<string, unknown>)[name];
    const cv = (input as Record<string, unknown>)[name];
    return bv !== cv;
  };
  const prov = (name: string) => provenance?.[name] ?? null;

  const update = useCallback(
    (key: keyof ScenarioInput, value: unknown) => {
      onChange({ ...input, [key]: value });
    },
    [input, onChange]
  );

  const currentMat = materials.find((m) => m.value === input.material);
  const validRC = currentMat?.valid_recycled_content ?? [0, 25, 30, 50, 75, 100];

  return (
    <div className="scenario-form">
      <ParameterGroup title="Material & Composition">
        <div className="field">
          <label>
            Material
            {prov("material") && <ProvenanceBadge source={prov("material")!.source} confidence={prov("material")!.confidence} notes={prov("material")!.notes} />}
          </label>
          <select
            value={input.material}
            onChange={(e) => {
              const mat = materials.find((m) => m.value === e.target.value);
              const newRC = mat?.valid_recycled_content.includes(input.recycled_content)
                ? input.recycled_content
                : mat?.valid_recycled_content[0] ?? 0;
              onChange({ ...input, material: e.target.value, recycled_content: newRC });
            }}
          >
            {materials.map((m) => (
              <option key={m.value} value={m.value}>
                {m.value}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>
            Recycled Content
            {prov("recycled_content") && <ProvenanceBadge source={prov("recycled_content")!.source} confidence={prov("recycled_content")!.confidence} notes={prov("recycled_content")!.notes} />}
          </label>
          <select
            value={input.recycled_content}
            onChange={(e) => update("recycled_content", Number(e.target.value))}
          >
            {validRC.map((rc) => (
              <option key={rc} value={rc}>
                {rc}%
                {currentMat?.carbon_intensities[rc] != null
                  ? ` (${currentMat.carbon_intensities[rc]} kg CO2e/kg)`
                  : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>
            Blank Type
            {prov("raw_material_blank_type") && <ProvenanceBadge source={prov("raw_material_blank_type")!.source} confidence={prov("raw_material_blank_type")!.confidence} notes={prov("raw_material_blank_type")!.notes} />}
          </label>
          <select
            value={input.raw_material_blank_type}
            onChange={(e) => update("raw_material_blank_type", e.target.value)}
          >
            {blankTypes.map((bt) => (
              <option key={bt.value} value={bt.value}>
                {bt.value}
              </option>
            ))}
          </select>
        </div>
      </ParameterGroup>

      <ParameterGroup title="Part Geometry & Yield">
        <SliderField
          label="Raw Material Mass"
          value={input.raw_material_mass}
          min={1}
          max={10000}
          step={1}
          unit="g"
          onChange={(v) => update("raw_material_mass", v)}
        />
        <SliderField
          label="Final Part Mass"
          value={input.final_part_mass ?? 0}
          min={0}
          max={10000}
          step={1}
          unit="g"
          onChange={(v) => update("final_part_mass", v || null)}
        />
        <SliderField
          label="Final Part Yield"
          value={input.final_part_yield}
          min={0}
          max={1}
          step={0.01}
          onChange={(v) => update("final_part_yield", v)}
        />
      </ParameterGroup>

      <ParameterGroup title="Forming Processes" defaultOpen={false}>
        <SliderField
          label="Forging Strikes"
          value={input.forging_strikes}
          min={0} max={100} step={1}
          onChange={(v) => update("forging_strikes", v)}
        />
        <SliderField
          label="Trimming/Bending Strikes"
          value={input.forging_trimming_bending_strikes}
          min={0} max={100} step={1}
          onChange={(v) => update("forging_trimming_bending_strikes", v)}
        />
        <SliderField
          label="Stamping Steps"
          value={input.stamping_steps}
          min={0} max={50} step={1}
          onChange={(v) => update("stamping_steps", v)}
        />
        <SliderField
          label="Injection Molding Parts/Shot"
          value={input.plastic_injection_molding_parts_per_shot}
          min={0} max={100} step={1}
          onChange={(v) => update("plastic_injection_molding_parts_per_shot", v)}
        />
        <SliderField
          label="Injection Molding Cycle Time"
          value={input.plastic_injection_molding_cycle_time}
          min={0} max={300} step={1}
          unit="sec"
          onChange={(v) => update("plastic_injection_molding_cycle_time", v)}
        />
      </ParameterGroup>

      <ParameterGroup title="Thermal Processes" defaultOpen={false}>
        <SliderField
          label="Annealing Steps"
          value={input.heat_treatment_annealing_steps}
          min={0} max={10} step={1}
          onChange={(v) => update("heat_treatment_annealing_steps", v)}
        />
        <SliderField
          label="Annealing Temperature"
          value={input.heat_treatment_annealing_temperature}
          min={0} max={1200} step={10}
          unit="\u00b0C"
          onChange={(v) => update("heat_treatment_annealing_temperature", v)}
        />
        <SliderField
          label="Tempering Steps"
          value={input.heat_treatment_tempering_steps}
          min={0} max={10} step={1}
          onChange={(v) => update("heat_treatment_tempering_steps", v)}
        />
        <SliderField
          label="Tempering Temperature"
          value={input.heat_treatment_tempering_temperature}
          min={0} max={600} step={10}
          unit="\u00b0C"
          onChange={(v) => update("heat_treatment_tempering_temperature", v)}
        />
      </ParameterGroup>

      <ParameterGroup title="Finishing Processes" defaultOpen={false}>
        <SliderField
          label="Machining Cycle Time"
          value={input.machining_cycle_time}
          min={0} max={3600} step={1}
          unit="sec"
          onChange={(v) => update("machining_cycle_time", v)}
        />
        <SliderField
          label="Laser Cut/Weld Time"
          value={input.laser_cutting_welding_cycle_time}
          min={0} max={600} step={1}
          unit="sec"
          onChange={(v) => update("laser_cutting_welding_cycle_time", v)}
        />
        <SliderField
          label="Laser Etching Time"
          value={input.laser_etching_cycle_time}
          min={0} max={300} step={1}
          unit="sec"
          onChange={(v) => update("laser_etching_cycle_time", v)}
        />
        <SliderField
          label="Sanding Time"
          value={input.sanding_cycle_time}
          min={0} max={300} step={1}
          unit="sec"
          onChange={(v) => update("sanding_cycle_time", v)}
        />
        <div className="field toggle-field">
          <label>Anodizing</label>
          <button
            className={`toggle ${input.anodizing ? "on" : ""}`}
            onClick={() => update("anodizing", !input.anodizing)}
          >
            {input.anodizing ? "ON" : "OFF"}
          </button>
        </div>
      </ParameterGroup>

      <ParameterGroup title="Electricity Grid">
        <div className="field">
          <label>Manufacturing Grid</label>
          <select
            value={input.electricity_grid}
            onChange={(e) => update("electricity_grid", e.target.value)}
          >
            {gridOptions.map((g) => (
              <option key={g.value} value={g.value}>
                {g.value} ({g.intensity} kg CO2e/kWh)
              </option>
            ))}
          </select>
        </div>
      </ParameterGroup>
    </div>
  );
}
