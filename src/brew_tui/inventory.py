"""Inventory data models, persistence, and conversational helpers."""


import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Self, Tuple


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
                    specialty_grains=[MaltItem(**g) for g in data.get("specialty_grains", [])],
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
            names = ", ".join(f"{g.name} ({g.amount_kg} kg)" for g in self.specialty_grains)
            lines.append(f"Specialty grains: {names}")
        if self.hops:
            names = ", ".join(f"{h.name} ({h.amount_g} g)" for h in self.hops)
            lines.append(f"Hops: {names}")
        if self.yeasts:
            names = ", ".join(f"{y.name} ({y.yeast_type})" for y in self.yeasts)
            lines.append(f"Yeast: {names}")
        return lines


# ── Parsing helpers for conversation input ────────────────────────────


def parse_malts(text: str) -> List[MaltItem]:
    items: List[MaltItem] = []
    for part in text.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, val = part.rsplit(":", 1)
        try:
            amount = float(val.strip())
        except ValueError:
            continue
        items.append(MaltItem(name=name.strip(), amount_kg=amount))
    return items


def parse_hops(text: str) -> List[HopItem]:
    items: List[HopItem] = []
    for part in text.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, val = part.rsplit(":", 1)
        try:
            amount = float(val.strip())
        except ValueError:
            continue
        items.append(HopItem(name=name.strip(), amount_g=amount))
    return items


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
    "Alright, let's get this inventory filled out!  "
    "Check the fridge, dig around in the closet, "
    "those ingredient packets get lost in there sometimes."
)

STAGES: List[dict] = [
    {
        "key": "malts",
        "title": "Malts",
        "prompt": (
            "What base and specialty malts do you have on hand?\n"
            "Enter them as [bold]name:kg[/] separated by commas.\n"
            "Example: [italic]Pale 2-Row:5, Munich:1, Crystal 60:0.3[/]\n\n"
            "Type [bold]skip[/] if you don't have any to add."
        ),
        "parser": parse_malts,
        "confirm": "Got it! Added {} to your malt stash.",
    },
    {
        "key": "hops",
        "title": "Hops",
        "prompt": (
            "Now hops! Same idea — [bold]name:grams[/] separated by commas.\n"
            "Example: [italic]Cascade:50, Citra:30, Saaz:40[/]\n\n"
            "Type [bold]skip[/] if none."
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
            "Type [bold]skip[/] if you don't have any right now."
        ),
        "parser": parse_yeasts,
        "confirm": "Added {} to your yeast collection!",
    },
    {
        "key": "specialty_grains",
        "title": "Specialty Grains",
        "prompt": (
            "Any specialty grains, flaked adjuncts, or oddball ingredients?\n"
            "Same [bold]name:kg[/] format as malts.\n"
            "Example: [italic]Flaked Oats:1, Rice Hulls:0.5, Cara-Pils:0.5[/]\n\n"
            "Type [bold]skip[/] to finish up."
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
