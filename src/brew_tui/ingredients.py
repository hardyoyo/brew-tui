"""Bundled common malt and hop data with fuzzy search.

At import time this module tries to load a beerproto-derived ingredient
lookup table from ``data/beerproto_ingredients.json``.  If that file
exists its values are authoritative; otherwise the module falls back to
the hardcoded values embedded below.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Malt:
    name: str
    ppg: float
    lovibond: float


@dataclass
class Hop:
    name: str
    alpha_acid_pct: float


# ── Fallback data (used only when beerproto_ingredients.json is absent) ─

_FALLBACK_MALTS = [
    Malt("Extra Light LME", 37, 1.5),
    Malt("Light LME", 36, 2),
    Malt("Amber LME", 35, 12),
    Malt("Dark LME", 34, 20),
    Malt("Wheat LME", 36, 3),
    Malt("Pilsner LME", 37, 1.5),
    Malt("Munich LME", 35, 9),
    Malt("Rye LME", 35, 4),
    Malt("Extra Light DME", 44, 2),
    Malt("Light DME", 44, 3),
    Malt("Amber DME", 43, 12),
    Malt("Dark DME", 42, 22),
    Malt("Wheat DME", 44, 3),
    Malt("Pilsner DME", 44, 2),
    Malt("Munich DME", 43, 9),
    Malt("Rye DME", 43, 4),
    Malt("Rice DME", 44, 1),
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
    Malt("Chocolate", 30, 259),
    Malt("Roasted Barley", 30, 300),
    Malt("Black Patent", 30, 370),
    Malt("Acidulated", 35, 3),
    Malt("Smoked", 37, 4),
]

_FALLBACK_HOPS = [
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


# ── Loader ───────────────────────────────────────────────────────────────

_DATA_PATH = Path(__file__).resolve().parent / "data" / "beerproto_ingredients.json"

_malts: Optional[List[Malt]] = None
_hops: Optional[List[Hop]] = None


def _load() -> None:
    global _malts, _hops

    if _malts is not None:
        return  # already loaded

    if _DATA_PATH.is_file():
        try:
            with open(_DATA_PATH) as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning("Failed to load %s: %s", _DATA_PATH, exc)
            data = {}

        malt_dict = data.get("malts", {})
        hop_dict = data.get("hops", {})

        if malt_dict:
            _malts = [
                Malt(
                    name=name,
                    ppg=info["ppg"],
                    lovibond=info["lovibond"],
                )
                for name, info in malt_dict.items()
            ]
        if hop_dict:
            _hops = [
                Hop(
                    name=name,
                    alpha_acid_pct=info["alpha_acid_pct"],
                )
                for name, info in hop_dict.items()
            ]

    if _malts is None:
        _malts = _FALLBACK_MALTS[:]
    if _hops is None:
        _hops = _FALLBACK_HOPS[:]


# ── Public API ───────────────────────────────────────────────────────────


def get_malts() -> List[Malt]:
    _load()
    assert _malts is not None
    return _malts[:]


def get_hops() -> List[Hop]:
    _load()
    assert _hops is not None
    return _hops[:]


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
