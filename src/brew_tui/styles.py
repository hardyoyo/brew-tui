"""BJCP style definitions, JSON loader, fallback data, and fuzzy search."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = "bjcp_styleguide-2021.json"


@dataclass
class Style:
    name: str
    category: str
    style_id: str
    og_min: float
    og_max: float
    ibu_min: float
    ibu_max: float
    srm_min: float
    srm_max: float
    abv_min: float
    abv_max: float

    # ── Range string helpers ────────────────────────────────

    def og_range_str(self) -> str:
        return f"{self.og_min:.3f} – {self.og_max:.3f}"

    def ibu_range_str(self) -> str:
        return f"{self.ibu_min:.0f} – {self.ibu_max:.0f}"

    def srm_range_str(self) -> str:
        return f"{self.srm_min:.0f} – {self.srm_max:.0f}"

    def abv_range_str(self) -> str:
        return f"{self.abv_min:.1f} – {self.abv_max:.1f}"

    # ── Boundary checks ─────────────────────────────────────

    def contains_og(self, sg: float) -> bool:
        return self.og_min <= sg <= self.og_max

    def contains_ibu(self, ibu: float) -> bool:
        return self.ibu_min <= ibu <= self.ibu_max

    def contains_srm(self, srm: float) -> bool:
        return self.srm_min <= srm <= self.srm_max

    # ── Status labels ───────────────────────────────────────

    def ibu_status(self, ibu: float) -> str:
        if ibu < self.ibu_min:
            return "below"
        if ibu > self.ibu_max:
            return "above"
        return "within"

    def srm_status(self, srm: float) -> str:
        if srm < self.srm_min:
            return "below"
        if srm > self.srm_max:
            return "above"
        return "within"

    def og_status(self, sg: float) -> str:
        if sg < self.og_min:
            return "below"
        if sg > self.og_max:
            return "above"
        return "within"


# ── JSON loader ────────────────────────────────────────────────────


def _parse_style(raw: dict) -> Optional[Style]:
    """Parse a single style dict, returning *None* if vital stats
    (OG, IBU, colour) are absent (e.g. specialty-type styles)."""
    try:
        og = raw["original_gravity"]
        ibu = raw["international_bitterness_units"]
        srm = raw["color"]
    except KeyError:
        return None

    abv = raw.get("alcohol_by_volume", {})

    return Style(
        name=raw["name"],
        category=raw.get("category", ""),
        style_id=raw["style_id"],
        og_min=og["minimum"]["value"],
        og_max=og["maximum"]["value"],
        ibu_min=ibu["minimum"]["value"],
        ibu_max=ibu["maximum"]["value"],
        srm_min=srm["minimum"]["value"],
        srm_max=srm["maximum"]["value"],
        abv_min=abv.get("minimum", {}).get("value", 0.0),
        abv_max=abv.get("maximum", {}).get("value", 0.0),
    )


def load_styles(data_dir: Optional[str] = None) -> List[Style]:
    """Load BJCP styles from the local JSON file, falling back to
    a built-in mini dataset if the file is unavailable."""
    target = Path(data_dir or DATA_DIR) / DATA_FILE

    if target.is_file():
        try:
            with open(target) as f:
                raw = json.load(f)
            styles = raw["beerjson"]["styles"]
            parsed: List[Style] = []
            for s in styles:
                sty = _parse_style(s)
                if sty is not None:
                    parsed.append(sty)
            if parsed:
                logger.info("Loaded %d styles from %s", len(parsed), target)
                return parsed
        except Exception as exc:
            logger.warning("Failed to parse %s: %s", target, exc)

    logger.info("Style file %s not found — using built-in fallback", target)
    return [_parse_style(s) for s in _FALLBACK_STYLES if _parse_style(s) is not None]


# ── Fuzzy search ───────────────────────────────────────────────────


def search_styles(styles: List[Style], query: str) -> List[Style]:
    """Filter *styles* by fuzzy or substring match on name.

    An empty *query* returns all styles unchanged.
    """
    if not query:
        return styles[:]

    q = query.lower()

    # exact substring matches first (sorted by position)
    exact = [s for s in styles if q in s.name.lower()]
    if exact:
        return exact

    # fall back to rapidfuzz when no substring hits
    try:
        from rapidfuzz import fuzz

        scored = [(s, fuzz.partial_ratio(q, s.name.lower())) for s in styles]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [s for s, score in scored if score >= 65]
    except ImportError:
        return []


# ── Embedded fallback (~30 common styles) ─────────────────────────

_FALLBACK_STYLES = [
    {
        "name": "American Light Lager",
        "category": "Standard American Beer",
        "style_id": "1A",
        "original_gravity": {"minimum": {"value": 1.028}, "maximum": {"value": 1.040}},
        "international_bitterness_units": {
            "minimum": {"value": 8},
            "maximum": {"value": 12},
        },
        "color": {"minimum": {"value": 2}, "maximum": {"value": 3}},
        "final_gravity": {"minimum": {"value": 0.998}, "maximum": {"value": 1.008}},
        "alcohol_by_volume": {"minimum": {"value": 2.8}, "maximum": {"value": 4.2}},
    },
    {
        "name": "American Lager",
        "category": "Standard American Beer",
        "style_id": "1B",
        "original_gravity": {"minimum": {"value": 1.040}, "maximum": {"value": 1.050}},
        "international_bitterness_units": {
            "minimum": {"value": 8},
            "maximum": {"value": 18},
        },
        "color": {"minimum": {"value": 2}, "maximum": {"value": 4}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.012}},
        "alcohol_by_volume": {"minimum": {"value": 4.2}, "maximum": {"value": 5.3}},
    },
    {
        "name": "Czech Premium Pale Lager",
        "category": "Czech Lager",
        "style_id": "3B",
        "original_gravity": {"minimum": {"value": 1.044}, "maximum": {"value": 1.060}},
        "international_bitterness_units": {
            "minimum": {"value": 30},
            "maximum": {"value": 45},
        },
        "color": {"minimum": {"value": 3.5}, "maximum": {"value": 6}},
        "final_gravity": {"minimum": {"value": 1.013}, "maximum": {"value": 1.017}},
        "alcohol_by_volume": {"minimum": {"value": 4.2}, "maximum": {"value": 5.8}},
    },
    {
        "name": "German Pilsner",
        "category": "German Lager",
        "style_id": "5D",
        "original_gravity": {"minimum": {"value": 1.044}, "maximum": {"value": 1.050}},
        "international_bitterness_units": {
            "minimum": {"value": 22},
            "maximum": {"value": 40},
        },
        "color": {"minimum": {"value": 2}, "maximum": {"value": 5}},
        "final_gravity": {"minimum": {"value": 1.006}, "maximum": {"value": 1.012}},
        "alcohol_by_volume": {"minimum": {"value": 4.4}, "maximum": {"value": 5.2}},
    },
    {
        "name": "Weissbier",
        "category": "German Wheat Beer",
        "style_id": "10A",
        "original_gravity": {"minimum": {"value": 1.044}, "maximum": {"value": 1.052}},
        "international_bitterness_units": {
            "minimum": {"value": 8},
            "maximum": {"value": 15},
        },
        "color": {"minimum": {"value": 2}, "maximum": {"value": 6}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.014}},
        "alcohol_by_volume": {"minimum": {"value": 4.3}, "maximum": {"value": 5.6}},
    },
    {
        "name": "British Pale Ale",
        "category": "British Pale Ale",
        "style_id": "11A",
        "original_gravity": {"minimum": {"value": 1.040}, "maximum": {"value": 1.055}},
        "international_bitterness_units": {
            "minimum": {"value": 20},
            "maximum": {"value": 40},
        },
        "color": {"minimum": {"value": 4}, "maximum": {"value": 11}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.015}},
        "alcohol_by_volume": {"minimum": {"value": 4.0}, "maximum": {"value": 5.5}},
    },
    {
        "name": "Irish Stout",
        "category": "Irish Beer",
        "style_id": "15B",
        "original_gravity": {"minimum": {"value": 1.036}, "maximum": {"value": 1.044}},
        "international_bitterness_units": {
            "minimum": {"value": 25},
            "maximum": {"value": 45},
        },
        "color": {"minimum": {"value": 25}, "maximum": {"value": 40}},
        "final_gravity": {"minimum": {"value": 1.007}, "maximum": {"value": 1.011}},
        "alcohol_by_volume": {"minimum": {"value": 3.8}, "maximum": {"value": 5.0}},
    },
    {
        "name": "American Pale Ale",
        "category": "American Pale Ale",
        "style_id": "18B",
        "original_gravity": {"minimum": {"value": 1.045}, "maximum": {"value": 1.060}},
        "international_bitterness_units": {
            "minimum": {"value": 30},
            "maximum": {"value": 50},
        },
        "color": {"minimum": {"value": 5}, "maximum": {"value": 10}},
        "final_gravity": {"minimum": {"value": 1.010}, "maximum": {"value": 1.015}},
        "alcohol_by_volume": {"minimum": {"value": 4.5}, "maximum": {"value": 6.2}},
    },
    {
        "name": "American Porter",
        "category": "American Porter",
        "style_id": "20A",
        "original_gravity": {"minimum": {"value": 1.050}, "maximum": {"value": 1.070}},
        "international_bitterness_units": {
            "minimum": {"value": 25},
            "maximum": {"value": 50},
        },
        "color": {"minimum": {"value": 22}, "maximum": {"value": 40}},
        "final_gravity": {"minimum": {"value": 1.012}, "maximum": {"value": 1.018}},
        "alcohol_by_volume": {"minimum": {"value": 4.8}, "maximum": {"value": 6.5}},
    },
    {
        "name": "American Stout",
        "category": "American Stout",
        "style_id": "20C",
        "original_gravity": {"minimum": {"value": 1.050}, "maximum": {"value": 1.075}},
        "international_bitterness_units": {
            "minimum": {"value": 35},
            "maximum": {"value": 60},
        },
        "color": {"minimum": {"value": 30}, "maximum": {"value": 40}},
        "final_gravity": {"minimum": {"value": 1.010}, "maximum": {"value": 1.022}},
        "alcohol_by_volume": {"minimum": {"value": 5.0}, "maximum": {"value": 7.0}},
    },
    {
        "name": "American IPA",
        "category": "IPA",
        "style_id": "21A",
        "original_gravity": {"minimum": {"value": 1.050}, "maximum": {"value": 1.070}},
        "international_bitterness_units": {
            "minimum": {"value": 40},
            "maximum": {"value": 70},
        },
        "color": {"minimum": {"value": 6}, "maximum": {"value": 14}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.015}},
        "alcohol_by_volume": {"minimum": {"value": 5.5}, "maximum": {"value": 7.5}},
    },
    {
        "name": "Double IPA",
        "category": "IPA",
        "style_id": "22A",
        "original_gravity": {"minimum": {"value": 1.060}, "maximum": {"value": 1.080}},
        "international_bitterness_units": {
            "minimum": {"value": 60},
            "maximum": {"value": 100},
        },
        "color": {"minimum": {"value": 6}, "maximum": {"value": 14}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.018}},
        "alcohol_by_volume": {"minimum": {"value": 6.5}, "maximum": {"value": 9.0}},
    },
    {
        "name": "Russian Imperial Stout",
        "category": "Strong American Ale",
        "style_id": "22C",
        "original_gravity": {"minimum": {"value": 1.075}, "maximum": {"value": 1.115}},
        "international_bitterness_units": {
            "minimum": {"value": 50},
            "maximum": {"value": 90},
        },
        "color": {"minimum": {"value": 30}, "maximum": {"value": 40}},
        "final_gravity": {"minimum": {"value": 1.018}, "maximum": {"value": 1.030}},
        "alcohol_by_volume": {"minimum": {"value": 8.0}, "maximum": {"value": 14.0}},
    },
    {
        "name": "Saison",
        "category": "French and Belgian Ale",
        "style_id": "25B",
        "original_gravity": {"minimum": {"value": 1.048}, "maximum": {"value": 1.065}},
        "international_bitterness_units": {
            "minimum": {"value": 20},
            "maximum": {"value": 35},
        },
        "color": {"minimum": {"value": 5}, "maximum": {"value": 14}},
        "final_gravity": {"minimum": {"value": 1.002}, "maximum": {"value": 1.008}},
        "alcohol_by_volume": {"minimum": {"value": 5.0}, "maximum": {"value": 7.0}},
    },
    {
        "name": "Belgian Dubbel",
        "category": "Belgian Strong Ale",
        "style_id": "26B",
        "original_gravity": {"minimum": {"value": 1.054}, "maximum": {"value": 1.068}},
        "international_bitterness_units": {
            "minimum": {"value": 15},
            "maximum": {"value": 25},
        },
        "color": {"minimum": {"value": 10}, "maximum": {"value": 17}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.018}},
        "alcohol_by_volume": {"minimum": {"value": 6.0}, "maximum": {"value": 7.6}},
    },
    {
        "name": "Belgian Tripel",
        "category": "Belgian Strong Ale",
        "style_id": "26C",
        "original_gravity": {"minimum": {"value": 1.070}, "maximum": {"value": 1.085}},
        "international_bitterness_units": {
            "minimum": {"value": 18},
            "maximum": {"value": 40},
        },
        "color": {"minimum": {"value": 4.5}, "maximum": {"value": 7}},
        "final_gravity": {"minimum": {"value": 1.008}, "maximum": {"value": 1.018}},
        "alcohol_by_volume": {"minimum": {"value": 7.5}, "maximum": {"value": 10.5}},
    },
]
