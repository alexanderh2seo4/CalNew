"""Concentration conversions. Matrix changes are intentionally unsupported."""
from __future__ import annotations

import math

R_GAS = 8.31446261815324  # Pa m3 / mol K


def _positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def to_ppbv(value: float, unit: str, *, molecular_weight: float | None = None,
            temperature_k: float | None = None, pressure_pa: float | None = None) -> float:
    _positive(value, "concentration")
    unit = unit.replace("µ", "u").replace("μ", "u").replace("³", "3").strip()
    if unit in ("ppbv", "nmol/mol"):
        return value
    if unit in ("ppmv", "umol/mol"):
        return value * 1000
    if unit == "mol/mol":
        return value * 1e9
    mass_scale = {"mg/m3": 1e-3, "ug/m3": 1e-6, "ng/m3": 1e-9, "g/m3": 1.0}
    if unit not in mass_scale:
        raise ValueError(f"Ambiguous or unsupported gas unit {unit!r}; supply an explicit gas basis")
    if molecular_weight is None or temperature_k is None or pressure_pa is None:
        raise ValueError("Gas mass conversion requires molecular weight, temperature and pressure")
    for val, name in [(molecular_weight, "molecular_weight"), (temperature_k, "temperature"), (pressure_pa, "pressure")]:
        _positive(val, name)
    return value * mass_scale[unit] / molecular_weight * R_GAS * temperature_k / pressure_pa * 1e9


def normalise_threshold(value: float, unit: str, matrix: str, **conditions) -> tuple[float, str]:
    _positive(value, "threshold")
    if matrix == "air":
        return math.log10(to_ppbv(value, unit, **conditions)), "log10(ppbv)"
    if matrix == "water":
        unit = unit.replace("µ", "u").replace("μ", "u")
        scales = {"mg/L": 1, "ug/L": 1e-3, "ng/L": 1e-6, "g/L": 1000}
        if unit not in scales:
            raise ValueError("Water thresholds require explicit mass/volume units; no air conversion is inferred")
        return math.log10(value * scales[unit]), "log10(mg/L)"
    raise ValueError(f"No normalisation is defined for matrix {matrix!r}")


def inverse_log_ppm_to_log_ppbv(value: float) -> float:
    """Abraham target log10(1 / ODT[ppmv]) -> log10(ODT[ppbv])."""
    if not math.isfinite(value):
        raise ValueError("Non-finite threshold")
    return 3.0 - value

