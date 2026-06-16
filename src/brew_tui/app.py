"""Main Textual TUI application for brew-tui."""


from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Input, Label, ListItem, ListView, Select, Static

from .config import BrewConfig
from .engine import _to_float, calculate_og, calculate_srm, calculate_ibu
from .ingredients import Malt, Hop, get_malts, get_hops, search_malts, search_hops
from .inventory import INVENTORY_FILENAME, Inventory
from .inventory_screen import InventoryScreen
from .styles import DATA_DIR, DATA_FILE, Style, load_styles, search_styles
from .widgets import GaugeBar


class BrewTUI(App):
    """Interactive homebrew recipe helper."""

    CSS_PATH = "brew_tui.tcss"
    BINDINGS = [
        ("ctrl+t", "cycle_theme", "Theme"),
        ("ctrl+i", "open_inventory", "Inventory"),
    ]

    def __init__(self, config: BrewConfig | None = None):
        super().__init__()
        self._config = config or BrewConfig.load()

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

    # ── ingredient reactives ──────────────────────────────────────────
    malt_query = reactive("")
    hop_query = reactive("")

    _painted = False
    _recalc_id = 0
    _all_styles: List[Style] = []
    _all_malts: List[Malt] = []
    _all_hops: List[Hop] = []

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
                yield Static("── Malts ──", id="malt-header")
                yield Input(id="malt-filter", placeholder="Search malts...")
                yield ListView(id="malt-list")
                yield Static("── Hops ──", id="hop-header")
                yield Input(id="hop-filter", placeholder="Search hops...")
                yield ListView(id="hop-list")

            with Vertical(id="right-pane"):
                yield Static("═══ Style Selector ═══", id="style-header")
                yield Input(id="style-filter", placeholder="Filter styles...")
                yield ListView(id="style-list")
                yield Static(id="style-info")
                yield Static("═══ Settings ═══", id="settings-header")
                yield Label("Theme")
                yield Select([], id="theme-select", prompt="Select theme...")
                yield Button("Build Inventory", id="btn-inventory", variant="primary")
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

        self._inventory = Inventory.load(
            Path(self._config.recipe_path) / INVENTORY_FILENAME
        )
        if not self._inventory.nonempty and (
            Path(self._config.recipe_path) / INVENTORY_FILENAME
        ).exists():
            self.notify(
                "Inventory file was corrupted — starting fresh",
                severity="warning",
                timeout=5,
            )

        style_file = Path(DATA_DIR) / DATA_FILE
        if not style_file.is_file():
            self.notify(
                "BJCP style data not found — using built-in styles",
                severity="warning",
                timeout=5,
            )

        self._all_malts = get_malts()
        self._all_hops = get_hops()
        if self._inventory.nonempty:
            for m in self._inventory.malts:
                self._all_malts.append(Malt(f"[I] {m.name}", m.ppg, m.lovibond))
            for m in self._inventory.specialty_grains:
                self._all_malts.append(Malt(f"[I] {m.name}", m.ppg, m.lovibond))
            for h in self._inventory.hops:
                self._all_hops.append(Hop(f"[I] {h.name}", h.alpha_acid_pct))
        self._populate_malt_list(self._all_malts)
        self._populate_hop_list(self._all_hops)

        self._config.ensure_dirs()
        theme_select = self.query_one("#theme-select", Select)
        themes = sorted(self.available_themes)
        theme_select.set_options([(t, t) for t in themes])
        if self._config.theme in themes:
            self.theme = self._config.theme
            theme_select.value = self._config.theme

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

    def _populate_malt_list(self, malts: List[Malt]) -> None:
        lv = self.query_one("#malt-list", ListView)
        lv.clear()
        for m in malts:
            lv.append(ListItem(Label(f"{m.name}  {m.lovibond:.0f}L  {m.ppg}PPG")))
        if malts:
            lv.index = 0

    def _populate_hop_list(self, hops: List[Hop]) -> None:
        lv = self.query_one("#hop-list", ListView)
        lv.clear()
        for h in hops:
            lv.append(ListItem(Label(f"{h.name}  {h.alpha_acid_pct:.1f}%")))
        if hops:
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
        elif input_id == "malt-filter":
            self.malt_query = raw
        elif input_id == "hop-filter":
            self.hop_query = raw

    # ── Style selection ──────────────────────────────────────────────

    def watch_style_query(self, query: str) -> None:
        if not self._painted:
            return
        matches = search_styles(self._all_styles, query)
        self._populate_style_list(matches)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            if event.list_view.id == "style-list":
                self.selected_style = None
            return
        lv = event.list_view
        if lv.index is None:
            return
        if lv.id == "style-list":
            matches = search_styles(self._all_styles, self.style_query)
            if lv.index < len(matches):
                self.selected_style = matches[lv.index]
        elif lv.id == "malt-list":
            matches = search_malts(self._all_malts, self.malt_query)
            if lv.index < len(matches):
                malt = matches[lv.index]
                self.query_one("#spec-lovibond", Input).value = str(malt.lovibond)
                self.query_one("#spec-malt", Input).focus()
        elif lv.id == "hop-list":
            matches = search_hops(self._all_hops, self.hop_query)
            if lv.index < len(matches):
                hop = matches[lv.index]
                self.query_one("#alpha-acid", Input).value = str(hop.alpha_acid_pct)
                self.query_one("#hop-weight", Input).focus()

    # ── Ingredient watchers ──────────────────────────────────────────

    def watch_malt_query(self, query: str) -> None:
        if not self._painted:
            return
        matches = search_malts(self._all_malts, query)
        self._populate_malt_list(matches)

    def watch_hop_query(self, query: str) -> None:
        if not self._painted:
            return
        matches = search_hops(self._all_hops, query)
        self._populate_hop_list(matches)

    # ── Inventory ────────────────────────────────────────────────────

    def action_open_inventory(self) -> None:
        self.push_screen(InventoryScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-inventory":
            self.push_screen(InventoryScreen())

    # ── Theme ────────────────────────────────────────────────────────

    def action_cycle_theme(self) -> None:
        themes = sorted(self.available_themes)
        current = self.theme
        idx = (themes.index(current) + 1) % len(themes) if current in themes else 0
        new_theme = themes[idx]
        self.theme = new_theme
        self._config.theme = new_theme
        self._config.save()
        self.query_one("#theme-select", Select).value = new_theme
        self.notify(f"Theme: {new_theme}", timeout=3)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "theme-select":
            self.theme = str(event.value)
            self._config.theme = str(event.value)
            self._config.save()
            self.notify(f"Theme: {str(event.value)}", timeout=3)

    @property
    def recipe_path(self) -> str:
        return self._config.recipe_path

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
