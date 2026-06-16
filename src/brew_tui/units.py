"""Unit conversion utilities for brew-tui."""

from enum import Enum


class UnitSystem(str, Enum):
    IMPERIAL = "imperial"
    METRIC = "metric"


LB_PER_KG = 2.20462
OZ_PER_G = 0.035274
GAL_PER_L = 0.264172

KG_PER_LB = 1.0 / LB_PER_KG
G_PER_OZ = 1.0 / OZ_PER_G
L_PER_GAL = 1.0 / GAL_PER_L


def kg_to_lb(kg: float) -> float:
    return kg * LB_PER_KG


def lb_to_kg(lb: float) -> float:
    return lb * KG_PER_LB


def g_to_oz(g: float) -> float:
    return g * OZ_PER_G


def oz_to_g(oz: float) -> float:
    return oz * G_PER_OZ


def l_to_gal(liters: float) -> float:
    return liters * GAL_PER_L


def gal_to_l(gallons: float) -> float:
    return gallons * L_PER_GAL
