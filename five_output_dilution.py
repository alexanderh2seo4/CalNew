#!/usr/bin/env python3
"""Nominal setpoint calculator for Olfactometer-Five-Output-Design.md.

Neat liquid only; ideal complete evaporation and zero sample losses.
No device communications or hardware control. Standard library only.
"""
import argparse
import json
import math

R_GAS = 8.314462618  # kPa L / (mol K)


def calculate(density, molecular_weight, syringe_ul_min, dilution_l_min,
              carrier_l_min=1.0, sample_l_min=0.5,
              background_l_min=110.0, temperature_c=22.0,
              pressure_kpa=101.325, ports=5):
    """Shared final mixer; all volume flows use the supplied common T/P."""
    positives = (density, molecular_weight, carrier_l_min, sample_l_min,
                 background_l_min, pressure_kpa)
    if any(not math.isfinite(x) or x <= 0 for x in positives):
        raise ValueError("Density, MW, flows and pressure must be finite and positive")
    if any(not math.isfinite(x) or x < 0 for x in
           (syringe_ul_min, dilution_l_min)):
        raise ValueError("Syringe rate and dilution flow must be finite and nonnegative")
    if not math.isfinite(temperature_c) or temperature_c <= -273.15:
        raise ValueError("Invalid reference temperature")
    if not isinstance(ports, int) or ports <= 0:
        raise ValueError("Port count must be a positive integer")
    molar_volume = R_GAS * (temperature_c + 273.15) / pressure_kpa
    mass_ug_min = 1000.0 * density * syringe_ul_min
    vapor_l_min = mass_ug_min * 1e-6 / molecular_weight * molar_volume
    source_l_min = carrier_l_min + vapor_l_min
    mixed_l_min = source_l_min + dilution_l_min
    excess_l_min = mixed_l_min - sample_l_min
    if excess_l_min <= 0:
        raise ValueError("Mixed supply must exceed shared sample demand for pressure regulation")
    final_flow = background_l_min + sample_l_min
    port_flow = final_flow / ports
    c_mg_m3 = mass_ug_min / mixed_l_min * sample_l_min / final_flow
    return {
        "status": "NOMINAL: complete evaporation and zero losses assumed",
        "ports": ports,
        "mass_feed_ug_min": mass_ug_min,
        "vapor_added_l_min": vapor_l_min,
        "electronic_dilution_factor": mixed_l_min / source_l_min,
        "excess_to_exhaust_l_min": excess_l_min,
        "shared_sample_l_min": sample_l_min,
        "shared_final_l_min": final_flow,
        "each_port_l_min": port_flow,
        "nominal_port_flow_meets_20_l_min": port_flow >= 20.0,
        "each_port_nominal_mg_m3": c_mg_m3,
        "each_port_nominal_ug_m3": c_mg_m3 * 1000.0,
        "each_port_nominal_ppb": c_mg_m3 * molar_volume * 1000.0 / molecular_weight,
        "analyte_to_all_ports_ug_min": mass_ug_min * sample_l_min / mixed_l_min,
        "analyte_to_exhaust_ug_min": mass_ug_min * excess_l_min / mixed_l_min,
    }


def solve_dilution(target_mg_m3, density, molecular_weight, syringe_ul_min,
                   carrier_l_min=1.0, sample_l_min=0.5,
                   background_l_min=110.0, temperature_c=22.0,
                   pressure_kpa=101.325, maximum_l_min=9.0, ports=5):
    """Solve attenuation at a chosen syringe rate; reject unreachable targets."""
    if not math.isfinite(target_mg_m3) or target_mg_m3 <= 0:
        raise ValueError("Target must be finite and positive; use a blank valve state for zero")
    if not math.isfinite(maximum_l_min) or maximum_l_min < 0:
        raise ValueError("Maximum dilution flow must be finite and nonnegative")
    base = calculate(density, molecular_weight, syringe_ul_min, 0,
                     carrier_l_min, sample_l_min, background_l_min,
                     temperature_c, pressure_kpa, ports)
    source_flow = carrier_l_min + base["vapor_added_l_min"]
    needed = (base["mass_feed_ug_min"] * sample_l_min /
              ((background_l_min + sample_l_min) * target_mg_m3) - source_flow)
    if needed < -1e-10 or needed > maximum_l_min + 1e-10:
        raise ValueError("Target outside electronic dilution range at this syringe rate")
    return min(maximum_l_min, max(0.0, needed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--density", type=float, required=True, help="g/mL")
    parser.add_argument("--mw", type=float, required=True, help="g/mol")
    parser.add_argument("--syringe", type=float, required=True, help="microlitres/min")
    parser.add_argument("--sample-flow", type=float, default=0.5,
                        help="shared takeoff L/min; default 0.5, qualified range modules only")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--dilution", type=float, help="clean dilution L/min")
    selection.add_argument("--target", type=float, help="target nominal mg/m3")
    args = parser.parse_args()
    try:
        qd = args.dilution
        if args.target is not None:
            qd = solve_dilution(args.target, args.density, args.mw, args.syringe,
                                sample_l_min=args.sample_flow)
        if qd > 9:
            raise ValueError("Design's proposed dilution limit is 9 L/min")
        result = calculate(args.density, args.mw, args.syringe, qd,
                           sample_l_min=args.sample_flow)
        result["set_dilution_l_min"] = qd
        print(json.dumps(result, indent=2))
    except ValueError as error:
        parser.error(str(error))
