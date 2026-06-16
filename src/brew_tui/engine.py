"""Calculation engine for brew-tui recipe helper."""

import math
from typing import List, Optional

DEFAULT_BASE_MALT_PPG = 37.0
DEFAULT_MASH_EFFICIENCY = 0.75
TINSETH_UTILIZATION = 0.24
MOREY_COEFF = 1.4922
MOREY_EXP = 0.6859
ABV_FACTOR = 131.25

KG_PER_LB = 2.20462
L_PER_GAL = 0.264172

FALLBACK_SAFE = 1.0


def _to_float(value, fallback=FALLBACK_SAFE) -> float:
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
    batch_l = _to_float(batch_size_l)
    total_mcu = 0.0
    for weight_kg, lovibond in zip(malt_weights_kg, malt_lovibonds):
        wt = _to_float(weight_kg, 0.0)
        lb = wt * KG_PER_LB
        gal = batch_l * L_PER_GAL
        total_mcu += lb * lovibond / gal
    return total_mcu


def calculate_srm_from_mcu(mcu: float) -> float:
    if mcu is None or mcu <= 0.0:
        return 0.0
    return round(1.4922 * (mcu**0.6859), 2)


def calculate_srm(
    malt_weights_kg: List[float],
    malt_lovibonds: List[float],
    batch_size_l: float,
) -> float:
    mcu = calculate_mcu(malt_weights_kg, malt_lovibonds, batch_size_l)
    return calculate_srm_from_mcu(mcu)


def calculate_ibu(
    hop_weight_g: float,
    alpha_acid_pct: float,
    batch_size_l: float,
    utilization: float = TINSETH_UTILIZATION,
) -> float:
    batch_l = _to_float(batch_size_l)
    hop_w = _to_float(hop_weight_g, 0.0)
    aa_decimal = alpha_acid_pct / 100.0
    ibu = (hop_w * aa_decimal * utilization * 1000.0) / batch_l
    return round(ibu, 1)


def calculate_abv(og: float, fg: float = 1.010) -> float:
    if og <= 0.0 or fg <= 0.0 or fg >= og:
        return 0.0
    return round((og - fg) * ABV_FACTOR, 2)


def tinseth_utilization(boil_time_min: float, sg_estimate: float = 1.050) -> float:
    if boil_time_min <= 0:
        return 0.0
    bigness = 1.65 * 0.000125 ** (sg_estimate - 1)
    boiltime = (1 - math.exp(-0.04 * boil_time_min)) / 4.15
    return min(bigness * boiltime, 0.50)


def calculate_ibu_multi(
    hop_additions: List[tuple[float, float, float]],
    batch_size_l: float,
    sg_estimate: float = 1.050,
) -> float:
    total = 0.0
    for weight_g, aa_pct, boil_min in hop_additions:
        u = tinseth_utilization(boil_min, sg_estimate)
        total += calculate_ibu(weight_g, aa_pct, batch_size_l, utilization=u)
    return round(total, 1)
