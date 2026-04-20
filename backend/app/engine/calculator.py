"""Core carbon footprint calculation engine — 11 process formulas.

This module is intentionally pure: no FastAPI, no IO, no environment variables.
All data is received via function parameters. All constants are documented below.
"""

from ..models.schemas import ScenarioInput, ProcessBreakdown, FormulaStep, FormulaTrace
from ..models.enums import BlankType
from ..config import MODEL_VERSION, DATA_VERSION
from .data_loader import LoadedData


# ---------------------------------------------------------------------------
# Constants sourced from Supporting_Data_1.csv
#
# These are hardcoded because the CSV "Data" column reuses generic keys
# (e.g. "Power", "Electricity") across multiple process rows.  Each value
# below is annotated with its CSV row number and process context.
# ---------------------------------------------------------------------------
CONSTANTS = {
    # Machining — row 20, "Power" under "Machining"
    "machining_power_kw": 2.0,
    # Laser cutting/welding — row 60, "Power" under "Laser cutting"
    "laser_cut_power_kw": 4.0,
    # Laser etching — row 62, "Power" under "Laser etching"
    "laser_etch_power_kw": 0.145,
    # Sanding — row 76, "Power" under "Sanding"
    "sanding_power_kw": 0.6,
    # Injection molding — row 58, "Power" under "Injection molding"
    "im_power_kw": 12.0,
    # Die casting electricity — row 47, "Electricity" under "Die casting (aluminum)"
    "dc_elec_kwh_per_kg": 0.97,
    # Die casting thermal energy — row 48, "Thermal energy" under "Die casting (aluminum)"
    "dc_thermal_mj_per_kg": 1.9,
    # Extrusion energy — row 68, "Electricity" under "Extrusion"
    "ext_energy_kwh_per_kg": 1.06,
    # Al sheet rolling energy — row 43, "Electricity" under "Al sheet rolling"
    "roll_energy_kwh_per_kg": 0.092,
    # Plastic specific heat — not in CSV, engineering estimate
    "plastic_specific_heat_j_per_kgk": 1200.0,
}

# Keys looked up from LoadedData.process_params (unique, unambiguous keys)
DATA_KEYS = {
    "forging_energy": "Forging strikes",             # row 22
    "bending_energy": "Trimming/bending strikes",    # row 23
    "stamping_energy": "Stamping presses",           # row 25
    "anodizing_energy": "Electricity",               # row 72 (under "Ano")
    "al_specific_heat": "Aluminum specific heat",    # row 32
    "heating_efficiency": "Heating efficiency",       # row 33
    "starting_temp": "Starting temperature",          # row 34
    "roll_addl_impact": "Add\u2019l impact",          # row 44 (right single quote)
    "dc_thermal_intensity": "Thermal intensity",       # row 49
}


def calculate_footprint(args: ScenarioInput, data: LoadedData) -> ProcessBreakdown:
    grid = data.grid_intensities.get(args.electricity_grid.value, 0.82)
    mass_kg = args.raw_material_mass / 1000.0
    pp = data.process_params
    C = CONSTANTS

    result = ProcessBreakdown()

    # 1. Raw Material
    rc_key = f"{args.recycled_content}%"
    ci = data.alloy_carbon_intensity.get(args.material.value, {}).get(rc_key)
    if ci is not None:
        result.raw_material = mass_kg * ci

    # 2. Upstream Processing
    result.upstream_processing = _calc_upstream(args, data, mass_kg, grid)

    # 3. Forging
    forging_energy = pp.get(DATA_KEYS["forging_energy"], 0.01)
    bending_energy = pp.get(DATA_KEYS["bending_energy"], 0.005)
    result.forging = (
        args.forging_strikes * forging_energy
        + args.forging_trimming_bending_strikes * bending_energy
    ) * grid

    # 4. Stamping
    stamping_energy = pp.get(DATA_KEYS["stamping_energy"], 0.005)
    result.stamping = mass_kg * stamping_energy * args.stamping_steps * grid

    # 5. Heat Treatment
    result.heat_treatment = _calc_heat_treatment(args, data, mass_kg, grid)

    # 6. Machining
    result.machining = (
        (args.machining_cycle_time / 3600.0) * C["machining_power_kw"] * grid
    )

    # 7. Laser (cutting/welding + etching)
    result.laser = (
        (args.laser_cutting_welding_cycle_time / 3600.0) * C["laser_cut_power_kw"] * grid
        + (args.laser_etching_cycle_time / 3600.0) * C["laser_etch_power_kw"] * grid
    )

    # 8. Sanding
    result.sanding = (
        (args.sanding_cycle_time / 3600.0) * C["sanding_power_kw"] * grid
    )

    # 9. Die Casting (only for Die cast blank type)
    if args.raw_material_blank_type == BlankType.DIE_CAST:
        dc_thermal_intensity = pp.get(DATA_KEYS["dc_thermal_intensity"], 0.0754)
        result.die_casting = mass_kg * (
            C["dc_elec_kwh_per_kg"] * grid
            + C["dc_thermal_mj_per_kg"] * dc_thermal_intensity
        )

    # 10. Injection Molding
    if (
        args.plastic_injection_molding_parts_per_shot > 0
        and args.plastic_injection_molding_cycle_time > 0
    ):
        result.injection_molding = (
            (args.plastic_injection_molding_cycle_time / 3600.0)
            * C["im_power_kw"]
            * grid
            / args.plastic_injection_molding_parts_per_shot
        )

    # 11. Anodizing
    if args.anodizing:
        ano_energy = pp.get(DATA_KEYS["anodizing_energy"], 0.2)
        result.anodizing = ano_energy * grid

    # Total
    result.total = (
        result.raw_material
        + result.upstream_processing
        + result.forging
        + result.stamping
        + result.heat_treatment
        + result.machining
        + result.laser
        + result.sanding
        + result.die_casting
        + result.injection_molding
        + result.anodizing
    )

    # Version stamp
    result.model_version = MODEL_VERSION
    result.data_version = DATA_VERSION
    result.assumptions_hash = data.assumptions_hash

    return result


def _calc_upstream(
    args: ScenarioInput, data: LoadedData, mass_kg: float, grid: float
) -> float:
    bt = args.raw_material_blank_type
    pp = data.process_params
    util = data.upstream_utilization.get(bt.value, {})
    C = CONSTANTS

    if bt == BlankType.EXTRUDED:
        ext_util = util.get("extrusion", 0.63)
        return (mass_kg / ext_util) * C["ext_energy_kwh_per_kg"] * grid

    elif bt in (BlankType.ROLLED_SHEET, BlankType.ROLLED_PLATE):
        roll_addl = pp.get(DATA_KEYS["roll_addl_impact"], 0.5748)
        roll_util = util.get("sheet_rolling", 0.71)
        return (mass_kg / roll_util) * (C["roll_energy_kwh_per_kg"] * grid + roll_addl)

    elif bt == BlankType.DIE_CAST:
        # Die casting forming energy handled in formula 9; upstream = 0 to avoid double count
        return 0.0

    elif bt == BlankType.INJECTION_MOLDED:
        return 0.0

    return 0.0


def _calc_heat_treatment(
    args: ScenarioInput, data: LoadedData, mass_kg: float, grid: float
) -> float:
    pp = data.process_params
    starting_temp = pp.get(DATA_KEYS["starting_temp"], 25.0)
    efficiency = pp.get(DATA_KEYS["heating_efficiency"], 0.20)

    mat = args.material.value
    if mat in ("PC", "TPU", "TPU bio-based"):
        specific_heat = CONSTANTS["plastic_specific_heat_j_per_kgk"]
    else:
        specific_heat = pp.get(DATA_KEYS["al_specific_heat"], 900.0)

    total = 0.0

    # Annealing
    if args.heat_treatment_annealing_steps > 0 and args.heat_treatment_annealing_temperature > 0:
        delta_t = args.heat_treatment_annealing_temperature - starting_temp
        energy_kwh = mass_kg * specific_heat * delta_t / (efficiency * 3_600_000)
        total += energy_kwh * args.heat_treatment_annealing_steps * grid

    # Tempering
    if args.heat_treatment_tempering_steps > 0 and args.heat_treatment_tempering_temperature > 0:
        delta_t = args.heat_treatment_tempering_temperature - starting_temp
        energy_kwh = mass_kg * specific_heat * delta_t / (efficiency * 3_600_000)
        total += energy_kwh * args.heat_treatment_tempering_steps * grid

    return total


def calculate_footprint_debug(args: ScenarioInput, data: LoadedData) -> FormulaTrace:
    """Calculate footprint with full step-by-step trace for auditing."""
    grid = data.grid_intensities.get(args.electricity_grid.value, 0.82)
    mass_kg = args.raw_material_mass / 1000.0
    pp = data.process_params
    C = CONSTANTS
    steps: list[FormulaStep] = []

    breakdown = ProcessBreakdown()

    # 1. Raw Material
    rc_key = f"{args.recycled_content}%"
    ci = data.alloy_carbon_intensity.get(args.material.value, {}).get(rc_key, 0.0)
    breakdown.raw_material = mass_kg * ci
    steps.append(FormulaStep(
        process="raw_material",
        formula="mass_kg * carbon_intensity",
        inputs={"raw_material_mass_g": args.raw_material_mass, "material": args.material.value,
                "recycled_content": rc_key, "carbon_intensity_kg_co2e_per_kg": ci},
        intermediate={"mass_kg": mass_kg},
        result=breakdown.raw_material,
    ))

    # 2. Upstream Processing
    bt = args.raw_material_blank_type
    util = data.upstream_utilization.get(bt.value, {})
    if bt == BlankType.EXTRUDED:
        ext_util = util.get("extrusion", 0.63)
        breakdown.upstream_processing = (mass_kg / ext_util) * C["ext_energy_kwh_per_kg"] * grid
        steps.append(FormulaStep(
            process="upstream_processing",
            formula="(mass_kg / extrusion_util) * ext_energy * grid",
            inputs={"mass_kg": mass_kg, "extrusion_util": ext_util,
                    "ext_energy_kwh_per_kg": C["ext_energy_kwh_per_kg"], "grid": grid},
            intermediate={"mass_over_util_kg": mass_kg / ext_util,
                          "energy_kwh": (mass_kg / ext_util) * C["ext_energy_kwh_per_kg"]},
            result=breakdown.upstream_processing,
        ))
    elif bt in (BlankType.ROLLED_SHEET, BlankType.ROLLED_PLATE):
        roll_addl = pp.get(DATA_KEYS["roll_addl_impact"], 0.5748)
        roll_util = util.get("sheet_rolling", 0.71)
        breakdown.upstream_processing = (mass_kg / roll_util) * (C["roll_energy_kwh_per_kg"] * grid + roll_addl)
        steps.append(FormulaStep(
            process="upstream_processing",
            formula="(mass_kg / roll_util) * (roll_energy * grid + roll_addl_impact)",
            inputs={"mass_kg": mass_kg, "roll_util": roll_util,
                    "roll_energy_kwh_per_kg": C["roll_energy_kwh_per_kg"],
                    "roll_addl_impact": roll_addl, "grid": grid},
            intermediate={"mass_over_util_kg": mass_kg / roll_util},
            result=breakdown.upstream_processing,
        ))
    else:
        steps.append(FormulaStep(
            process="upstream_processing",
            formula="0 (blank_type has no upstream semi-fabrication or is handled by die_casting)",
            inputs={"blank_type": bt.value},
            intermediate={},
            result=0.0,
        ))

    # 3. Forging
    forging_energy = pp.get(DATA_KEYS["forging_energy"], 0.01)
    bending_energy = pp.get(DATA_KEYS["bending_energy"], 0.005)
    strike_kwh = args.forging_strikes * forging_energy
    bend_kwh = args.forging_trimming_bending_strikes * bending_energy
    breakdown.forging = (strike_kwh + bend_kwh) * grid
    steps.append(FormulaStep(
        process="forging",
        formula="(strikes * energy_per_strike + bending * energy_per_bending) * grid",
        inputs={"forging_strikes": args.forging_strikes, "energy_per_strike_kwh": forging_energy,
                "bending_strikes": args.forging_trimming_bending_strikes,
                "energy_per_bending_kwh": bending_energy, "grid": grid},
        intermediate={"strike_energy_kwh": strike_kwh, "bending_energy_kwh": bend_kwh,
                      "total_energy_kwh": strike_kwh + bend_kwh},
        result=breakdown.forging,
    ))

    # 4. Stamping
    stamping_energy = pp.get(DATA_KEYS["stamping_energy"], 0.005)
    breakdown.stamping = mass_kg * stamping_energy * args.stamping_steps * grid
    steps.append(FormulaStep(
        process="stamping",
        formula="mass_kg * energy_per_press * steps * grid",
        inputs={"mass_kg": mass_kg, "energy_per_press_kwh": stamping_energy,
                "stamping_steps": args.stamping_steps, "grid": grid},
        intermediate={"energy_before_grid": mass_kg * stamping_energy * args.stamping_steps},
        result=breakdown.stamping,
    ))

    # 5. Heat Treatment
    starting_temp = pp.get(DATA_KEYS["starting_temp"], 25.0)
    efficiency = pp.get(DATA_KEYS["heating_efficiency"], 0.20)
    mat = args.material.value
    specific_heat = (CONSTANTS["plastic_specific_heat_j_per_kgk"]
                     if mat in ("PC", "TPU", "TPU bio-based")
                     else pp.get(DATA_KEYS["al_specific_heat"], 900.0))
    ht_total = 0.0
    ht_intermediates: dict = {"specific_heat": specific_heat, "efficiency": efficiency,
                               "starting_temp": starting_temp}
    if args.heat_treatment_annealing_steps > 0 and args.heat_treatment_annealing_temperature > 0:
        delta_t = args.heat_treatment_annealing_temperature - starting_temp
        energy_kwh = mass_kg * specific_heat * delta_t / (efficiency * 3_600_000)
        anneal_result = energy_kwh * args.heat_treatment_annealing_steps * grid
        ht_total += anneal_result
        ht_intermediates["anneal_delta_t"] = delta_t
        ht_intermediates["anneal_energy_kwh"] = energy_kwh
        ht_intermediates["anneal_result"] = anneal_result
    if args.heat_treatment_tempering_steps > 0 and args.heat_treatment_tempering_temperature > 0:
        delta_t = args.heat_treatment_tempering_temperature - starting_temp
        energy_kwh = mass_kg * specific_heat * delta_t / (efficiency * 3_600_000)
        temper_result = energy_kwh * args.heat_treatment_tempering_steps * grid
        ht_total += temper_result
        ht_intermediates["temper_delta_t"] = delta_t
        ht_intermediates["temper_energy_kwh"] = energy_kwh
        ht_intermediates["temper_result"] = temper_result
    breakdown.heat_treatment = ht_total
    steps.append(FormulaStep(
        process="heat_treatment",
        formula="mass_kg * specific_heat * delta_T / (efficiency * 3600000) * steps * grid",
        inputs={"mass_kg": mass_kg, "anneal_steps": args.heat_treatment_annealing_steps,
                "anneal_temp": args.heat_treatment_annealing_temperature,
                "temper_steps": args.heat_treatment_tempering_steps,
                "temper_temp": args.heat_treatment_tempering_temperature, "grid": grid},
        intermediate=ht_intermediates,
        result=breakdown.heat_treatment,
    ))

    # 6. Machining
    breakdown.machining = (args.machining_cycle_time / 3600.0) * C["machining_power_kw"] * grid
    steps.append(FormulaStep(
        process="machining",
        formula="(cycle_time_s / 3600) * power_kw * grid",
        inputs={"cycle_time_s": args.machining_cycle_time, "power_kw": C["machining_power_kw"], "grid": grid},
        intermediate={"hours": args.machining_cycle_time / 3600.0,
                      "energy_kwh": (args.machining_cycle_time / 3600.0) * C["machining_power_kw"]},
        result=breakdown.machining,
    ))

    # 7. Laser
    cut_result = (args.laser_cutting_welding_cycle_time / 3600.0) * C["laser_cut_power_kw"] * grid
    etch_result = (args.laser_etching_cycle_time / 3600.0) * C["laser_etch_power_kw"] * grid
    breakdown.laser = cut_result + etch_result
    steps.append(FormulaStep(
        process="laser",
        formula="(cut_time/3600 * cut_power + etch_time/3600 * etch_power) * grid",
        inputs={"cut_time_s": args.laser_cutting_welding_cycle_time, "cut_power_kw": C["laser_cut_power_kw"],
                "etch_time_s": args.laser_etching_cycle_time, "etch_power_kw": C["laser_etch_power_kw"], "grid": grid},
        intermediate={"cut_result": cut_result, "etch_result": etch_result},
        result=breakdown.laser,
    ))

    # 8. Sanding
    breakdown.sanding = (args.sanding_cycle_time / 3600.0) * C["sanding_power_kw"] * grid
    steps.append(FormulaStep(
        process="sanding",
        formula="(cycle_time_s / 3600) * power_kw * grid",
        inputs={"cycle_time_s": args.sanding_cycle_time, "power_kw": C["sanding_power_kw"], "grid": grid},
        intermediate={"energy_kwh": (args.sanding_cycle_time / 3600.0) * C["sanding_power_kw"]},
        result=breakdown.sanding,
    ))

    # 9. Die Casting
    if args.raw_material_blank_type == BlankType.DIE_CAST:
        dc_thermal_intensity = pp.get(DATA_KEYS["dc_thermal_intensity"], 0.0754)
        breakdown.die_casting = mass_kg * (C["dc_elec_kwh_per_kg"] * grid + C["dc_thermal_mj_per_kg"] * dc_thermal_intensity)
        steps.append(FormulaStep(
            process="die_casting",
            formula="mass_kg * (dc_elec * grid + dc_thermal * thermal_intensity)",
            inputs={"mass_kg": mass_kg, "dc_elec_kwh_per_kg": C["dc_elec_kwh_per_kg"],
                    "dc_thermal_mj_per_kg": C["dc_thermal_mj_per_kg"],
                    "thermal_intensity": dc_thermal_intensity, "grid": grid},
            intermediate={"elec_component": mass_kg * C["dc_elec_kwh_per_kg"] * grid,
                          "thermal_component": mass_kg * C["dc_thermal_mj_per_kg"] * dc_thermal_intensity},
            result=breakdown.die_casting,
        ))
    else:
        steps.append(FormulaStep(
            process="die_casting", formula="0 (blank_type != Die cast)",
            inputs={"blank_type": args.raw_material_blank_type.value}, intermediate={}, result=0.0))

    # 10. Injection Molding
    if args.plastic_injection_molding_parts_per_shot > 0 and args.plastic_injection_molding_cycle_time > 0:
        breakdown.injection_molding = (
            (args.plastic_injection_molding_cycle_time / 3600.0) * C["im_power_kw"] * grid
            / args.plastic_injection_molding_parts_per_shot
        )
        steps.append(FormulaStep(
            process="injection_molding",
            formula="(cycle_time/3600 * power * grid) / parts_per_shot",
            inputs={"cycle_time_s": args.plastic_injection_molding_cycle_time,
                    "power_kw": C["im_power_kw"],
                    "parts_per_shot": args.plastic_injection_molding_parts_per_shot, "grid": grid},
            intermediate={"energy_kwh": (args.plastic_injection_molding_cycle_time / 3600.0) * C["im_power_kw"]},
            result=breakdown.injection_molding,
        ))
    else:
        steps.append(FormulaStep(
            process="injection_molding", formula="0 (parts_per_shot or cycle_time is 0)",
            inputs={}, intermediate={}, result=0.0))

    # 11. Anodizing
    if args.anodizing:
        ano_energy = pp.get(DATA_KEYS["anodizing_energy"], 0.2)
        breakdown.anodizing = ano_energy * grid
        steps.append(FormulaStep(
            process="anodizing", formula="energy_kwh * grid",
            inputs={"energy_kwh": ano_energy, "grid": grid}, intermediate={},
            result=breakdown.anodizing,
        ))
    else:
        steps.append(FormulaStep(
            process="anodizing", formula="0 (anodizing disabled)",
            inputs={}, intermediate={}, result=0.0))

    # Total + version
    breakdown.total = sum([
        breakdown.raw_material, breakdown.upstream_processing, breakdown.forging,
        breakdown.stamping, breakdown.heat_treatment, breakdown.machining,
        breakdown.laser, breakdown.sanding, breakdown.die_casting,
        breakdown.injection_molding, breakdown.anodizing,
    ])
    breakdown.model_version = MODEL_VERSION
    breakdown.data_version = DATA_VERSION
    breakdown.assumptions_hash = data.assumptions_hash

    return FormulaTrace(
        steps=steps,
        breakdown=breakdown,
        constants_used=CONSTANTS,
        grid_intensity=grid,
        mass_kg=mass_kg,
    )
