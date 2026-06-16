"""Bundled common malt and hop data with fuzzy search."""

from dataclasses import dataclass
from typing import List


@dataclass
class Malt:
    name: str
    ppg: float
    lovibond: float


@dataclass
class Hop:
    name: str
    alpha_acid_pct: float


# ── Malts ──────────────────────────────────────────────────────────────

_COMMON_MALTS = [
    Malt("Pale 2-Row", 37, 2),
    Malt("Pale 6-Row", 35, 2),
    Malt("Pilsner", 37, 1.5),
    Malt("Vienna", 36, 4),
    Malt("Munich", 35, 9),
    Malt("Maris Otter", 38, 3),
    Malt("Wheat Malt", 38, 2),
    Malt("Flaked Wheat", 37, 2),
    Malt("Flaked Oats", 33, 2),
    Malt("Crystal 20", 34, 20),
    Malt("Crystal 40", 34, 40),
    Malt("Crystal 60", 34, 60),
    Malt("Crystal 80", 34, 80),
    Malt("Cara-Pils", 33, 2),
    Malt("CaraMunich I", 33, 35),
    Malt("CaraMunich II", 33, 45),
    Malt("CaraMunich III", 33, 60),
    Malt("CaraAroma", 33, 130),
    Malt("Special B", 30, 150),
    Malt("Biscuit", 34, 25),
    Malt("Victory", 34, 28),
    Malt("Aromatic", 35, 26),
    Malt("Melanoidin", 35, 28),
    Malt("Honey", 34, 25),
    Malt("Chocolate", 30, 350),
    Malt("Roasted Barley", 30, 500),
    Malt("Black Patent", 30, 500),
    Malt("Acidulated", 35, 3),
    Malt("Smoked", 37, 4),
]

_COMMON_HOPS = [
    Hop("Cascade", 5.5),
    Hop("Centennial", 10.0),
    Hop("Chinook", 12.0),
    Hop("Citra", 13.0),
    Hop("Mosaic", 12.0),
    Hop("Simcoe", 13.0),
    Hop("Amarillo", 9.0),
    Hop("Columbus", 14.0),
    Hop("Magnum", 13.0),
    Hop("Saaz", 3.5),
    Hop("Hallertau Mittelfrüh", 4.0),
    Hop("Tettnang", 4.5),
    Hop("East Kent Golding", 5.0),
    Hop("Fuggle", 4.5),
    Hop("Willamette", 5.0),
    Hop("Northern Brewer", 8.0),
    Hop("Perle", 8.0),
    Hop("Target", 11.0),
    Hop("Styrian Golding", 5.0),
    Hop("Motueka", 7.0),
    Hop("Nelson Sauvin", 12.0),
    Hop("Galaxy", 14.0),
    Hop("Sorachi Ace", 12.0),
    Hop("Glacier", 6.0),
    Hop("Mt. Hood", 5.5),
    Hop("Sterling", 7.0),
]


def get_malts() -> List[Malt]:
    return _COMMON_MALTS[:]


def get_hops() -> List[Hop]:
    return _COMMON_HOPS[:]


def search_malts(malts: List[Malt], query: str) -> List[Malt]:
    if not query:
        return malts[:]
    q = query.lower()
    exact = [m for m in malts if q in m.name.lower()]
    if exact:
        return exact
    scored = _fuzzy_score([(m.name, m) for m in malts], q)
    return [m for m, s in scored if s >= 65]


def search_hops(hops: List[Hop], query: str) -> List[Hop]:
    if not query:
        return hops[:]
    q = query.lower()
    exact = [h for h in hops if q in h.name.lower()]
    if exact:
        return exact
    scored = _fuzzy_score([(h.name, h) for h in hops], q)
    return [h for h, s in scored if s >= 65]


def _fuzzy_score(
    items: List[tuple[str, object]], query: str
) -> List[tuple[object, int]]:
    try:
        from rapidfuzz import fuzz

        scored = [(obj, fuzz.partial_ratio(query, name.lower())) for name, obj in items]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored
    except ImportError:
        return []
