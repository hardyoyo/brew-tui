"""Main Textual TUI application for brew-tui."""

from __future__ import annotations

from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Input, Label, ListItem, ListView, Static

from .engine import _to_float, calculate_og, calculate_srm, calculate_ibu
from .styles import Style, load_styles, search_styles
from .widgets import GaugeBar


class BrewTUI(App):
    """Interactive homebrew recipe helper."""

    CSS_PATH = "brew_tui.tcss"

    # ── input reactives ──────────────────────────────────────────────
    batch_size_l       = reactive(20.0)
    base_malt_kg       = reactive(5.0)
    spec_malt_kg       = reactive(0.0)
    spec_malt_lovibond = reactive(10.0)
    hop_weight_g       = reactive(30.0)
    alpha_acid_pct     = reactive(5.0)

    # ── result reactives ─────────────────────────────────────────────
    og  = reactive(0.0)
    srm = reactive(0.0)
    ibu = reactive(0.0)

    # ── style reactives ──────────────────────────────────────────────
    selected_style = reactive(None)  # type: Optional[Style]
    style_query = reactive("")

    _painted = False
    _recalc_id = 0
    _all_styles: List[Style] = []

    # ── Composable widgets ───────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="left-pane"):
                yield Label("Batch Size (L)")
                yield Input(id="batch-size", value="20.0")
                yield Label("Base Malt (kg)")
                yield Input(id="base-malt", value="5.0")
                yield Label("Specialty Malt (kg)")
                yield Input(id="spec-malt", value="0.0")
                yield Label("Spec Malt Lovibond")
                yield Input(id="spec-lovibond", value="10.0")
                yield Label("Hop Weight (g)")
                yield Input(id="hop-weight", value="30.0")
                yield Label("Alpha Acid (%)")
                yield Input(id="alpha-acid", value="5.0")

            with Vertical(id="right-pane"):
                yield Static("═══ Style Selector ═══", id="style-header")
                yield Input(id="style-filter", placeholder="Filter styles...")
                yield ListView(id="style-list")
                yield Static(id="style-info")
                yield Static("═══ Dashboard ═══", id="dashboard-header")
                yield Static("OG:  —", id="og-display")
                yield GaugeBar(id="og-gauge")
                yield Static("SRM: —", id="srm-display")
                yield GaugeBar(id="srm-gauge")
                yield Static("IBU: —", id="ibu-display")
                yield GaugeBar(id="ibu-gauge")

        yield Footer()

    # ── Mount ────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._all_styles = load_styles()
        self._populate_style_list(self._all_styles)
        for gauge_id in ("#og-gauge", "#srm-gauge", "#ibu-gauge"):
            self.query_one(gauge_id, GaugeBar).display = False
        self._painted = True
        self._recalc()

    def _require_recalc(self) -> None:
        """Request a recalc with recursion guard."""
        if self._recalc_id:
            return
        self._recalc_id += 1
        try:
            self._recalc()
        finally:
            self._recalc_id -= 1

    def _populate_style_list(self, styles: List[Style]) -> None:
        """Replace the style list with a new set of items."""
        lv = self.query_one("#style-list", ListView)
        lv.clear()
        for s in styles:
            lv.append(ListItem(Label(f"{s.style_id} {s.name}")))
        if styles:
            lv.index = 0

    # ── Input handling ───────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        raw = event.value
        input_id = event.input.id
        if input_id == "batch-size":
            self.batch_size_l = _to_float(raw)
        elif input_id == "base-malt":
            self.base_malt_kg = _to_float(raw, 0.0)
        elif input_id == "spec-malt":
            self.spec_malt_kg = _to_float(raw, 0.0)
        elif input_id == "spec-lovibond":
            self.spec_malt_lovibond = _to_float(raw, 0.0)
        elif input_id == "hop-weight":
            self.hop_weight_g = _to_float(raw, 0.0)
        elif input_id == "alpha-acid":
            self.alpha_acid_pct = _to_float(raw, 0.0)
        elif input_id == "style-filter":
            self.style_query = raw

    # ── Style selection ──────────────────────────────────────────────

    def watch_style_query(self, query: str) -> None:
        if not self._painted:
            return
        matches = search_styles(self._all_styles, query)
        self._populate_style_list(matches)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            self.selected_style = None
            return
        lv = self.query_one("#style-list", ListView)
        if lv.index is None:
            return
        matches = search_styles(self._all_styles, self.style_query)
        if lv.index < len(matches):
            self.selected_style = matches[lv.index]

    # ── Reactive watchers ────────────────────────────────────────────

    def watch_selected_style(self, style: Optional[Style]) -> None:
        if not self._painted:
            return
        self._update_style_info(style)
        self._update_gauge_targets(style)
        self._refresh_all_displays()

    def watch_batch_size_l(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_base_malt_kg(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_spec_malt_kg(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_spec_malt_lovibond(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_hop_weight_g(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_alpha_acid_pct(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    def watch_og(self, value: float) -> None:
        if self._painted:
            self._refresh_display("og-display", "OG", value, ".4f")
            if self.selected_style:
                self.query_one("#og-gauge", GaugeBar).value = value

    def watch_srm(self, value: float) -> None:
        if self._painted:
            self._refresh_display("srm-display", "SRM", value, ".2f")
            if self.selected_style:
                self.query_one("#srm-gauge", GaugeBar).value = value

    def watch_ibu(self, value: float) -> None:
        if self._painted:
            self._refresh_display("ibu-display", "IBU", value, ".1f")
            if self.selected_style:
                self.query_one("#ibu-gauge", GaugeBar).value = value

    # ── Display helpers ──────────────────────────────────────────────

    def _refresh_display(
        self, widget_id: str, label: str, value: float, fmt: str
    ) -> None:
        """Update a Static display widget with or without style context."""
        style = self.selected_style
        w = self.query_one(f"#{widget_id}", Static)
        if style is None:
            w.update(f"{label}: {value:{fmt}}")
            return

        lo = getattr(style, f"{widget_id.split('-')[0]}_min")
        hi = getattr(style, f"{widget_id.split('-')[0]}_max")

        if value < lo:
            status = "[bold blue]below[/]"
        elif value > hi:
            status = "[bold red]above[/]"
        else:
            status = "[bold green]within[/]"

        w.update(f"{label}: {value:{fmt}}  {status}  {lo:{fmt}}–{hi:{fmt}}")

    def _update_style_info(self, style: Optional[Style]) -> None:
        info = self.query_one("#style-info", Static)
        if style is None:
            info.update("No style selected")
            return
        info.update(
            f"[bold]{style.name}[/]  ({style.style_id})\n"
            f"OG {style.og_range_str()}  "
            f"IBU {style.ibu_range_str()}  "
            f"SRM {style.srm_range_str()}  "
            f"ABV {style.abv_range_str()}"
        )

    def _update_gauge_targets(self, style: Optional[Style]) -> None:
        if style is None:
            for gid in ("#og-gauge", "#srm-gauge", "#ibu-gauge"):
                self.query_one(gid, GaugeBar).display = False
            return

        for prefix, attr in [("og", "og"), ("srm", "srm"), ("ibu", "ibu")]:
            g = self.query_one(f"#{prefix}-gauge", GaugeBar)
            g.display = True
            g.value = getattr(self, attr)
            g.minimum = getattr(style, f"{attr}_min")
            g.maximum = getattr(style, f"{attr}_max")

    def _refresh_all_displays(self) -> None:
        for wid, label, fmt in [
            ("og-display", "OG", ".4f"),
            ("srm-display", "SRM", ".2f"),
            ("ibu-display", "IBU", ".1f"),
        ]:
            self._refresh_display(wid, label, getattr(self, label.lower()), fmt)

    # ── Calculation ──────────────────────────────────────────────────

    def _recalc(self) -> None:
        self.og = calculate_og(
            [self.base_malt_kg, self.spec_malt_kg],
            self.batch_size_l,
        )
        self.srm = calculate_srm(
            [self.spec_malt_kg],
            [self.spec_malt_lovibond],
            self.batch_size_l,
        )
        self.ibu = calculate_ibu(
            self.hop_weight_g,
            self.alpha_acid_pct,
            self.batch_size_l,
        )
