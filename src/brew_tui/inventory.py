"""Inventory data models, persistence, and conversational helpers."""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Self


@dataclass
class MaltItem:
    name: str
    amount_kg: float = 0.0
    lovibond: float = 2.0
    ppg: float = 37.0


@dataclass
class HopItem:
    name: str
    amount_g: float = 0.0
    alpha_acid_pct: float = 5.0


@dataclass
class YeastItem:
    name: str
    yeast_type: str = "ale"
    packages: int = 1


@dataclass
class Inventory:
    malts: List[MaltItem] = field(default_factory=list)
    hops: List[HopItem] = field(default_factory=list)
    yeasts: List[YeastItem] = field(default_factory=list)
    specialty_grains: List[MaltItem] = field(default_factory=list)

    @property
    def nonempty(self) -> bool:
        return bool(self.malts or self.hops or self.yeasts or self.specialty_grains)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> Self:
        if path.is_file():
            try:
                with open(path) as f:
                    data = json.load(f)
                return cls(
                    malts=[MaltItem(**m) for m in data.get("malts", [])],
                    hops=[HopItem(**h) for h in data.get("hops", [])],
                    yeasts=[YeastItem(**y) for y in data.get("yeasts", [])],
                    specialty_grains=[
                        MaltItem(**g) for g in data.get("specialty_grains", [])
                    ],
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return cls()

    def summary_lines(self) -> List[str]:
        lines = []
        if self.malts:
            names = ", ".join(f"{m.name} ({m.amount_kg} kg)" for m in self.malts)
            lines.append(f"Malts: {names}")
        if self.specialty_grains:
            names = ", ".join(
                f"{g.name} ({g.amount_kg} kg)" for g in self.specialty_grains
            )
            lines.append(f"Specialty grains: {names}")
        if self.hops:
            names = ", ".join(f"{h.name} ({h.amount_g} g)" for h in self.hops)
            lines.append(f"Hops: {names}")
        if self.yeasts:
            names = ", ".join(f"{y.name} ({y.yeast_type})" for y in self.yeasts)
            lines.append(f"Yeast: {names}")
        return lines


# ── Parsing helpers for conversation input ────────────────────────────


_WEIGHT_RE = re.compile(r"^([\d.]+)\s*(kg|lb|lbs|oz|g)?$", re.IGNORECASE)


def _parse_weight(raw: str, default_unit: str = "kg") -> tuple[float, str] | None:
    m = _WEIGHT_RE.match(raw.strip())
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(2) or default_unit).lower()
    return val, unit


def _parse_malt_item(part: str) -> MaltItem | None:
    part = part.strip()
    if not part:
        return None
    if ":" not in part:
        return MaltItem(name=part)
    name, val = part.rsplit(":", 1)
    parsed = _parse_weight(val, "kg")
    if parsed is None:
        return None
    amount, unit = parsed
    if unit in ("lb", "lbs"):
        amount *= 0.453592
    elif unit == "oz":
        amount *= 0.0283495
    return MaltItem(name=name.strip(), amount_kg=round(amount, 3))


def parse_malts(text: str) -> List[MaltItem]:
    return [m for part in text.split(",") if (m := _parse_malt_item(part)) is not None]


def _parse_hop_item(part: str) -> HopItem | None:
    part = part.strip()
    if not part:
        return None
    if ":" not in part:
        return HopItem(name=part)
    name, val = part.rsplit(":", 1)
    parsed = _parse_weight(val, "g")
    if parsed is None:
        return None
    amount, unit = parsed
    if unit in ("lb", "lbs"):
        amount *= 453.592
    elif unit == "oz":
        amount *= 28.3495
    elif unit == "kg":
        amount *= 1000
    return HopItem(name=name.strip(), amount_g=round(amount, 1))


def parse_hops(text: str) -> List[HopItem]:
    return [h for part in text.split(",") if (h := _parse_hop_item(part)) is not None]


def parse_yeasts(text: str) -> List[YeastItem]:
    items: List[YeastItem] = []
    for part in text.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, val = part.rsplit(":", 1)
        ytype = val.strip().lower()
        if ytype not in ("ale", "lager"):
            ytype = "ale"
        items.append(YeastItem(name=name.strip(), yeast_type=ytype))
    return items


def parse_specialty_grains(text: str) -> List[MaltItem]:
    return parse_malts(text)


# ── Conversation stages ──────────────────────────────────────────────

STAGE_WELCOME = (
    "Let's keep track of what ingredients you have on hand!\n\n"
    "The amount is [bold]optional[/] — if you know it, great. "
    "It's only used by the (underdeveloped) inventory tracker. "
    "Otherwise just enter ingredient names and skip the amounts."
)


def _build_stages(imperial: bool = False) -> List[dict]:
    malt_unit = "lb" if imperial else "kg"
    malt_example = (
        "Pale 2-Row:11, Munich:2.2, Crystal 60:0.66"
        if imperial
        else "Pale 2-Row:5, Munich:1, Crystal 60:0.3"
    )
    hop_unit = "oz" if imperial else "grams"
    hop_example = (
        "Cascade:1.8, Citra:1.1, Saaz:1.4"
        if imperial
        else "Cascade:50, Citra:30, Saaz:40"
    )
    grain_example = (
        "Flaked Oats:2.2, Rice Hulls:1.1, Cara-Pils:1.1"
        if imperial
        else "Flaked Oats:1, Rice Hulls:0.5, Cara-Pils:0.5"
    )

    return [
        {
            "key": "malts",
            "title": "Malts",
            "prompt": (
                "What base and specialty malts do you have on hand?\n"
                f"Enter [bold]name[/] or [bold]name:{malt_unit}[/] separated by commas.\n"
                f"Example: [italic]{malt_example}[/]\n\n"
                "The amount is optional — it's only used for inventory tracking.\n"
                "You can also use [bold]kg[/], [bold]lb[/], or [bold]oz[/] suffixes.\n"
                "Type [bold]skip[/] to move on, or [bold]back[/] to go to the previous section."
            ),
            "parser": parse_malts,
            "confirm": "Got it! Added {} to your malt stash.",
        },
        {
            "key": "hops",
            "title": "Hops",
            "prompt": (
                f"Now hops! Same idea — [bold]name[/] or [bold]name:{hop_unit}[/] separated by commas.\n"
                f"Example: [italic]{hop_example}[/]\n\n"
                "The amount is optional — it's only used for inventory tracking.\n"
                "You can also use [bold]g[/], [bold]oz[/], [bold]lb[/], or [bold]kg[/] suffixes.\n"
                "Type [bold]skip[/] to move on, or [bold]back[/] to go to the previous section."
            ),
            "parser": parse_hops,
            "confirm": "Nice! Added {} to your hop inventory.",
        },
        {
            "key": "yeasts",
            "title": "Yeast",
            "prompt": (
                "Yeast time — [bold]name:type[/] where type is [bold]ale[/] or [bold]lager[/].\n"
                "Example: [italic]SafAle US-05:ale, WLP029:lager[/]\n\n"
                "Type [bold]skip[/] to move on, or [bold]back[/] to go to the previous section."
            ),
            "parser": parse_yeasts,
            "confirm": "Added {} to your yeast collection!",
        },
        {
            "key": "specialty_grains",
            "title": "Specialty Grains",
            "prompt": (
                "Any specialty grains, flaked adjuncts, or oddball ingredients?\n"
                f"Same [bold]name[/] or [bold]name:{malt_unit}[/] format as malts.\n"
                f"Example: [italic]{grain_example}[/]\n\n"
                "Type [bold]skip[/] to finish up, or [bold]back[/] to go to the previous section."
            ),
            "parser": parse_specialty_grains,
            "confirm": "Added {} as specialty grains!",
        },
    ]


STAGE_DONE = (
    "All done! Your inventory has been saved.\n\n"
    "Press [bold]Esc[/] to go back to the main screen. "
    "Your ingredients will show up in the browser lists marked with [bold][I][/]."
)

INVENTORY_FILENAME = "inventory.json"


def inventory_path(base_dir: Path) -> Path:
    return base_dir / INVENTORY_FILENAME
