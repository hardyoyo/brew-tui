"""Calculation engine for brew-tui recipe helper.

Provides OG, SRM, and IBU calculations with input-safety guards.
"""

from typing import List, Optional

DEFAULT_BASE_MALT_PPG = 37.0
DEFAULT_MASH_EFFICIENCY = 0.75
TINSETH_UTILIZATION = 0.24  # simplified 60-min boil utilization
MOREY_COEFF = 1.4922
MOREY_EXP = 0.6859

KG_PER_LB = 2.20462
L_PER_GAL = 0.264172

FALLBACK_SAFE = 1.0


def _to_float(value, fallback=FALLBACK_SAFE) -> float:
    """Safely convert a value to float, returning *fallback* on
    None, empty string, zero, or non-numeric input."""
    if value is None:
        return fallback
    if isinstance(value, str) and value.strip() == "":
        return fallback
    try:
        v = float(value)
    except (ValueError, TypeError):
        return fallback
    if v == 0.0:
        return fallback
    return v


def calculate_og(
    malt_weights_kg: List[float],
    batch_size_l: float,
    efficiency: float = DEFAULT_MASH_EFFICIENCY,
    potentials_ppg: Optional[List[float]] = None,
) -> float:
    """Calculate Original Gravity using PPG-based formula.

    SG = 1 + sum(malt_kg * 2.20462 * ppg * efficiency)
            / (batch_L * 0.264172) / 1000

    Returns OG as specific gravity (e.g. 1.050).
    """
    batch_l = _to_float(batch_size_l)
    if potentials_ppg is None:
        potentials_ppg = [DEFAULT_BASE_MALT_PPG] * len(malt_weights_kg)

    total_points = 0.0
    for weight_kg, ppg in zip(malt_weights_kg, potentials_ppg):
        wt = _to_float(weight_kg, 0.0)
        points = wt * KG_PER_LB * ppg * efficiency
        points /= batch_l * L_PER_GAL
        total_points += points

    return round(1.0 + total_points / 1000.0, 4)


def calculate_mcu(
    malt_weights_kg: List[float],
    malt_lovibonds: List[float],
    batch_size_l: float,
) -> float:
    """Malt Colour Units via MCU = sum(malt_lb * lovibond) / vol_gal."""
    batch_l = _to_float(batch_size_l)
    total_mcu = 0.0
    for weight_kg, lovibond in zip(malt_weights_kg, malt_lovibonds):
        wt = _to_float(weight_kg, 0.0)
        lb = wt * KG_PER_LB
        gal = batch_l * L_PER_GAL
        total_mcu += lb * lovibond / gal
    return total_mcu


def calculate_srm_from_mcu(mcu: float) -> float:
    """Convert MCU to SRM via the Morey equation.

    SRM = 1.4922 * (MCU ** 0.6859)

    Guards: if MCU <= 0 return 0.0 to prevent domain errors."""
    if mcu is None or mcu <= 0.0:
        return 0.0
    return round(1.4922 * (mcu**0.6859), 2)


def calculate_srm(
    malt_weights_kg: List[float],
    malt_lovibonds: List[float],
    batch_size_l: float,
) -> float:
    """Convenience: compute MCU then SRM."""
    mcu = calculate_mcu(malt_weights_kg, malt_lovibonds, batch_size_l)
    return calculate_srm_from_mcu(mcu)


def calculate_ibu(
    hop_weight_g: float,
    alpha_acid_pct: float,
    batch_size_l: float,
    utilization: float = TINSETH_UTILIZATION,
) -> float:
    """Calculate IBU using a simplified Tinseth formula.

    IBU = (hop_g * AA_decimal * utilization * 1000) / batch_L

    *alpha_acid_pct* is a percentage (e.g. 5.0 for 5% AA).
    *utilization* is a decimal (default 0.24 for 60-min boil).
    The factor 1000 handles US-to-metric unit conversion.
    """
    batch_l = _to_float(batch_size_l)
    hop_w = _to_float(hop_weight_g, 0.0)
    aa_decimal = alpha_acid_pct / 100.0
    ibu = (hop_w * aa_decimal * utilization * 1000.0) / batch_l
    return round(ibu, 1)
