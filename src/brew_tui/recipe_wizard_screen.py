"""Conversational recipe wizard screen."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from .ingredients import Malt, Hop, search_malts, search_hops
from .styles import Style, search_styles
from .units import l_to_gal, gal_to_l, lb_to_kg, oz_to_g

_WEIGHT_RE = re.compile(r"^([\d.]+)\s*(gal|l|oz|lb|lbs|kg|g|#)?$", re.IGNORECASE)
_HOP_TIME_RE = re.compile(r"@\s*([\d.]+)\s*(min(?:ute)?s?)?", re.IGNORECASE)
_WELCOME = (
    "Welcome to the Brew Wizard!\n\n"
    "I'll guide you through creating a recipe step by step.\n"
    "Answer each question, or type [bold]skip[/] to move on.\n"
    "Type [bold]back[/] to go to the previous question."
)


@dataclass
class WizardResult:
    style_name: Optional[str] = None
    batch_size_l: float = 20.0
    malt_additions: List[dict] = field(default_factory=list)
    hop_additions: List[dict] = field(default_factory=list)
    yeast: Optional[str] = None
    pitching_temp: Optional[str] = None
    fermentation_time: Optional[str] = None
    notes: Optional[str] = None


class RecipeWizardScreen(Screen):
    """Conversational wizard for creating a new recipe."""

    BINDINGS = [
        ("escape", "dismiss_wizard", "Return"),
    ]

    def __init__(
        self,
        styles: List[Style],
        malts: List[Malt],
        hops: List[Hop],
        imperial: bool = False,
    ):
        super().__init__()
        self._styles = styles
        self._malts = malts
        self._hops = hops
        self._imperial = imperial
        self._result = WizardResult()
        self._stage = -1
        self._stages = self._build_stages()

    def compose(self) -> ComposeResult:
        yield Header("Brew Wizard")
        yield RichLog(id="conv-log", highlight=True, markup=True, wrap=True)
        yield Input(id="conv-input", placeholder="Type your answer here...")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write("[bold yellow]Brewer[/]  " + _WELCOME)
        self._next_stage()

    def action_dismiss_wizard(self) -> None:
        self.dismiss(None)

    def _next_stage(self) -> None:
        self._stage += 1
        if self._stage >= len(self._stages):
            self._finish()
            return
        self._show_stage()

    def _prev_stage(self) -> None:
        self._stage -= 1
        self._show_stage()

    def _show_stage(self) -> None:
        stage = self._stages[self._stage]
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write(f"[bold yellow]Brewer[/]  Let's talk [bold]{stage['title']}[/]!")
        log.write("[bold yellow]Brewer[/]  " + stage["prompt"])
        inp = self.query_one("#conv-input", Input)
        inp.clear()
        inp.focus()

    def _finish(self) -> None:
        self.dismiss(self._result)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        inp = self.query_one("#conv-input", Input)
        inp.clear()
        log = self.query_one("#conv-log", RichLog)
        log.write(f"[bold cyan]You[/]  {text}")

        if self._stage >= len(self._stages):
            return

        if text.lower() in ("back", "prev", "previous"):
            if self._stage > 0:
                log.write("[bold yellow]Brewer[/]  Sure, let's go back!")
                self._prev_stage()
            else:
                log.write("[bold yellow]Brewer[/]  You're at the start already!")
                inp.focus()
            return

        if text.lower() in ("skip", "done", "none", "pass", ""):
            log.write("[bold yellow]Brewer[/]  No problem! Moving on...")
            self._next_stage()
            return

        stage = self._stages[self._stage]
        result = stage["parser"](text)
        if result is None:
            log.write(
                "[bold yellow]Brewer[/]  "
                "Hmm, I couldn't understand that. Try a different format, "
                "or type [bold]skip[/]."
            )
            inp.focus()
            return

        key = stage["key"]
        if key == "style":
            self._result.style_name = result
            log.write(f"[bold yellow]Brewer[/]  [bold]{result}[/] — excellent choice!")
        elif key == "batch_size":
            self._result.batch_size_l = result
            display = l_to_gal(result) if self._imperial else result
            unit = "gal" if self._imperial else "L"
            log.write(f"[bold yellow]Brewer[/]  Got it! {display:.1f} {unit} batch.")
        elif key in ("base_malts", "specialty_malts"):
            if result:
                self._result.malt_additions.extend(result)
                names = ", ".join(f"[bold]{m['name']}[/]" for m in result)
                log.write(f"[bold yellow]Brewer[/]  Added: {names}")
        elif key == "hops":
            if result:
                self._result.hop_additions.extend(result)
                names = ", ".join(f"[bold]{h['name']}[/]" for h in result)
                log.write(f"[bold yellow]Brewer[/]  Added: {names}")
        elif key == "yeast":
            self._result.yeast = result
            log.write(f"[bold yellow]Brewer[/]  [bold]{result}[/] — nice choice!")
        elif key == "pitching_temp":
            self._result.pitching_temp = result
            log.write("[bold yellow]Brewer[/]  Noted, I'll save that!")
        elif key == "fermentation_time":
            self._result.fermentation_time = result
            log.write("[bold yellow]Brewer[/]  Got it!")
        elif key == "notes":
            self._result.notes = result
            log.write("[bold yellow]Brewer[/]  Thanks, I'll save that with the recipe!")

        self._next_stage()

    # ── Stage definitions ──────────────────────────────────────────

    def _build_stages(self) -> List[dict]:
        batch_unit = "gal" if self._imperial else "L"
        batch_default = "5" if self._imperial else "20"
        malt_unit = "lbs" if self._imperial else "kg"
        hop_unit = "oz" if self._imperial else "g"
        malt_example = (
            f"Pale 2-Row:10 {malt_unit}, Vienna:2 {malt_unit}"
            if self._imperial
            else f"Pale 2-Row:5 {malt_unit}, Vienna:1 {malt_unit}"
        )
        hop_example = (
            f"Cascade:1 {hop_unit} @ 60, Citra:0.5 {hop_unit} @ 5"
            if self._imperial
            else f"Cascade:30 {hop_unit} @ 60, Citra:15 {hop_unit} @ 5"
        )

        return [
            {
                "key": "style",
                "title": "Style",
                "prompt": (
                    "What style are you brewing?\n"
                    "You can type a style name like [bold]American IPA[/], [bold]Kolsch[/], "
                    "or even a BJCP code like [bold]21B[/]."
                ),
                "parser": self._parse_style,
            },
            {
                "key": "batch_size",
                "title": "Batch Size",
                "prompt": (f"What batch size? (e.g., {batch_default} {batch_unit})"),
                "parser": self._parse_batch_size,
            },
            {
                "key": "base_malts",
                "title": "Base Malts",
                "prompt": (
                    "What base malts?\n"
                    f"Enter as: [bold]name: weight[/] (e.g., {malt_example})\n"
                    "Separate multiple with commas.\n"
                    "Type [bold]skip[/] if you'll add them later."
                ),
                "parser": self._parse_malts,
            },
            {
                "key": "specialty_malts",
                "title": "Specialty Malts",
                "prompt": (
                    "What specialty, crystal, or roasted malts?\n"
                    f"Same format: [bold]name: weight[/] (e.g., Crystal 60:0.5 {malt_unit}, "
                    f"Roasted Barley:4 oz)\n"
                    "Type [bold]skip[/] if none."
                ),
                "parser": self._parse_malts,
            },
            {
                "key": "hops",
                "title": "Hops & Schedule",
                "prompt": (
                    "What hops and schedule?\n"
                    f"Enter as: [bold]name: weight @ minutes[/] "
                    f"(e.g., {hop_example})\n"
                    "If you don't specify time, 60 min is assumed.\n"
                    "Type [bold]skip[/] if you'll add them later."
                ),
                "parser": self._parse_hops,
            },
            {
                "key": "yeast",
                "title": "Yeast",
                "prompt": (
                    "What yeast strain? (e.g., Safale US-05, WLP001, Wyeast 1056)\n"
                    "Type [bold]skip[/] if unsure."
                ),
                "parser": self._parse_text,
            },
            {
                "key": "pitching_temp",
                "title": "Pitching Temperature",
                "prompt": (
                    "What pitching temperature? (e.g., 68°F, 20°C)\n"
                    "Type [bold]skip[/] if unsure."
                ),
                "parser": self._parse_text,
            },
            {
                "key": "fermentation_time",
                "title": "Fermentation Time",
                "prompt": (
                    "How long does it typically take to ferment?\n"
                    "(e.g., 2 weeks, 14 days)\n"
                    "Type [bold]skip[/] if unsure."
                ),
                "parser": self._parse_text,
            },
            {
                "key": "notes",
                "title": "Notes",
                "prompt": (
                    "Any other notes? (e.g., dry hop schedule, water profile, "
                    "fermentation temp, special instructions)\n"
                    "Type [bold]skip[/] if none."
                ),
                "parser": self._parse_text,
            },
        ]

    # ── Parsers ───────────────────────────────────────────────────

    def _parse_style(self, text: str) -> Optional[str]:
        for s in self._styles:
            if s.style_id.lower() == text.lower():
                return s.name
        matches = search_styles(self._styles, text)
        if matches:
            return matches[0].name
        return None

    def _parse_batch_size(self, text: str) -> Optional[float]:
        m = _WEIGHT_RE.match(text.strip())
        if not m:
            return None
        value = float(m.group(1))
        unit = (m.group(2) or "").lower()
        if unit in ("gal",):
            return gal_to_l(value)
        elif unit in ("l",):
            return value
        elif unit in ("qt", "quarts"):
            return value * 0.946353
        else:
            return gal_to_l(value) if self._imperial else value

    @staticmethod
    def _parse_weight(raw: str) -> tuple[float, str] | None:
        m = _WEIGHT_RE.match(raw.strip())
        if m:
            return float(m.group(1)), (m.group(2) or "").lower()
        return None

    @staticmethod
    def _to_kg(amount: float, unit: str) -> float:
        if unit in ("lb", "lbs", "#"):
            return lb_to_kg(amount)
        elif unit == "oz":
            return amount * 0.0283495
        return amount

    @staticmethod
    def _to_g(amount: float, unit: str) -> float:
        if unit == "oz":
            return oz_to_g(amount)
        elif unit in ("lb", "lbs"):
            return amount * 453.592
        elif unit in ("kg",):
            return amount * 1000
        return amount

    def _lookup_malt(self, name: str) -> tuple[float, float]:
        matches = search_malts(self._malts, name)
        if matches:
            m = matches[0]
            return m.lovibond, m.ppg
        return 2.0, 37.0

    def _lookup_hop(self, name: str) -> float:
        matches = search_hops(self._hops, name)
        if matches:
            return matches[0].alpha_acid_pct
        return 10.0

    def _parse_malt_item(self, raw: str) -> Optional[dict]:
        raw = raw.strip()
        if not raw:
            return None
        parts = raw.rsplit(":", 1)
        if len(parts) == 2:
            name = parts[0].strip()
            w = self._parse_weight(parts[1].strip())
            if not w:
                return None
            amount, unit = w
            weight_kg = self._to_kg(amount, unit)
        else:
            name = raw
            weight_kg = lb_to_kg(1.0) if self._imperial else 1.0
        lovibond, ppg = self._lookup_malt(name)
        return {
            "name": name,
            "weight_kg": weight_kg,
            "lovibond": lovibond,
            "ppg": ppg,
        }

    def _parse_malts(self, text: str) -> Optional[List[dict]]:
        items = [i.strip() for i in text.split(",") if i.strip()]
        if not items:
            return None
        result = []
        for item in items:
            parsed = self._parse_malt_item(item)
            if parsed:
                result.append(parsed)
        return result if result else None

    def _parse_hop_item(self, raw: str) -> Optional[dict]:
        raw = raw.strip()
        if not raw:
            return None
        boil_time = 60.0
        time_m = _HOP_TIME_RE.search(raw)
        if time_m:
            boil_time = float(time_m.group(1))
            raw = _HOP_TIME_RE.sub("", raw).strip()
        parts = raw.rsplit(":", 1)
        if len(parts) == 2:
            name = parts[0].strip()
            w = self._parse_weight(parts[1].strip())
            if not w:
                return None
            amount, unit = w
            weight_g = self._to_g(amount, unit)
        else:
            name = raw
            weight_g = oz_to_g(1.0) if self._imperial else 30.0
        alpha = self._lookup_hop(name)
        return {
            "name": name,
            "weight_g": weight_g,
            "alpha_acid_pct": alpha,
            "boil_time_min": boil_time,
        }

    def _parse_hops(self, text: str) -> Optional[List[dict]]:
        items = [i.strip() for i in text.split(",") if i.strip()]
        if not items:
            return None
        result = []
        for item in items:
            parsed = self._parse_hop_item(item)
            if parsed:
                result.append(parsed)
        return result if result else None

    @staticmethod
    def _parse_text(text: str) -> Optional[str]:
        return text.strip() or None
