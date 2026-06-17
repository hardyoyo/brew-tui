"""Main Textual TUI application for brew-tui."""

import json
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Header,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
)

from .config import BrewConfig
from .engine import (
    calculate_abv,
    calculate_ibu_multi,
    calculate_og,
    calculate_srm,
)
from .ingredients import Malt, Hop, get_malts, get_hops, search_malts, search_hops
from .inventory import inventory_path, Inventory
from .inventory_edit_screen import InventoryEditScreen
from .inventory_screen import InventoryScreen
from .recipe_io_screen import OpenRecipeScreen, SaveAsScreen
from .recipe_wizard_screen import RecipeWizardScreen, WizardResult
from .styles import DATA_DIR, DATA_FILE, Style, load_styles, search_styles
from .units import (
    UnitSystem,
    gal_to_l,
    g_to_oz,
    kg_to_lb,
    l_to_gal,
    lb_to_kg,
    oz_to_g,
)
from .widgets import GaugeBar


class MaltAddition:
    __next_uid = 0

    def __init__(self, name: str, weight_kg: float, lovibond: float, ppg: float):
        self.uid = MaltAddition.__next_uid
        MaltAddition.__next_uid += 1
        self.name = name
        self.weight_kg = weight_kg
        self.lovibond = lovibond
        self.ppg = ppg


class HopAddition:
    __next_uid = 0

    def __init__(
        self,
        name: str,
        weight_g: float,
        alpha_acid_pct: float,
        boil_time_min: float = 60.0,
    ):
        self.uid = HopAddition.__next_uid
        HopAddition.__next_uid += 1
        self.name = name
        self.weight_g = weight_g
        self.alpha_acid_pct = alpha_acid_pct
        self.boil_time_min = boil_time_min


class MaltRow(Horizontal):
    def __init__(self, addition: MaltAddition, imperial: bool):
        super().__init__(classes="malt-row")
        self._addition = addition
        self._imperial = imperial

    def compose(self) -> ComposeResult:
        wt = (
            kg_to_lb(self._addition.weight_kg)
            if self._imperial
            else self._addition.weight_kg
        )
        yield Label(
            f"{self._addition.name}  ({self._addition.lovibond:.0f}L, {self._addition.ppg}PPG)",
            classes="malt-row-name",
        )
        yield Input(
            value=f"{wt:.3f}",
            id=f"malt-wt-{self._addition.uid}",
            classes="malt-row-wt",
        )
        yield Button("✕", id=f"malt-rm-{self._addition.uid}", classes="row-rm-btn")


class HopRow(Horizontal):
    def __init__(self, addition: HopAddition, imperial: bool):
        super().__init__(classes="hop-row")
        self._addition = addition
        self._imperial = imperial

    def compose(self) -> ComposeResult:
        wt = (
            g_to_oz(self._addition.weight_g)
            if self._imperial
            else self._addition.weight_g
        )
        yield Label(
            f"{self._addition.name}  ({self._addition.alpha_acid_pct:.1f}%)",
            classes="hop-row-name",
        )
        yield Input(
            value=f"{wt:.2f}",
            id=f"hop-wt-{self._addition.uid}",
            classes="hop-row-wt",
        )
        yield Input(
            value=str(self._addition.boil_time_min),
            id=f"hop-time-{self._addition.uid}",
            classes="hop-row-time",
        )
        yield Button("✕", id=f"hop-rm-{self._addition.uid}", classes="row-rm-btn")


class BrewTUI(App):
    """Interactive homebrew recipe helper."""

    CSS_PATH = "brew_tui.tcss"
    BINDINGS = [
        ("ctrl+t", "focus_theme", "Theme"),
        ("ctrl+i", "open_inventory", "Build Inventory"),
        ("ctrl+e", "edit_inventory", "Edit Inventory"),
        ("ctrl+w", "open_wizard", "Brew Wizard"),
        ("ctrl+n", "new_recipe", "New Recipe"),
        ("ctrl+s", "save_recipe_as", "Save As"),
        ("ctrl+o", "open_recipe", "Open"),
        ("ctrl+f", "focus_style_filter", "Style Search"),
        ("ctrl+u", "toggle_units", "Toggle Units"),
    ]

    def __init__(self, config: BrewConfig | None = None):
        super().__init__()
        self._config = config or BrewConfig.load()

    batch_size_l = reactive(20.0)
    mash_efficiency_pct = reactive(75.0)
    fg_estimate = reactive(1.010)

    og = reactive(0.0)
    srm = reactive(0.0)
    ibu = reactive(0.0)
    abv = reactive(0.0)

    selected_style: Optional[Style] = reactive(None)
    style_query = reactive("")
    malt_query = reactive("")
    hop_query = reactive("")

    _painted = False
    _recalc_id = 0
    _all_styles: List[Style] = []
    _all_malts: List[Malt] = []
    _all_hops: List[Hop] = []
    _malt_additions: List[MaltAddition] = []
    _hop_additions: List[HopAddition] = []
    _current_recipe_name: Optional[str] = None
    _recipe_style_name: Optional[str] = None
    _recipe_yeast: Optional[str] = None
    _recipe_pitching_temp: Optional[str] = None
    _recipe_fermentation_time: Optional[str] = None
    _recipe_notes: Optional[str] = None

    def _imperial(self) -> bool:
        return self._config.unit_system == UnitSystem.IMPERIAL

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="left-pane"):
                yield Label("Batch Size (L)", id="batch-size-label")
                yield Input(id="batch-size", value="20.0")

                yield Static("── Malt Additions ──", id="malt-add-header")
                yield Vertical(id="malt-additions")
                yield Input(id="malt-filter", placeholder="Search malts to add...")
                yield ListView(id="malt-list")

                yield Static("── Hop Additions ──", id="hop-add-header")
                yield Vertical(id="hop-additions")
                yield Input(id="hop-filter", placeholder="Search hops to add...")
                yield ListView(id="hop-list")

                yield Label("FG Estimate")
                yield Input(id="fg-estimate", value="1.010")
                yield Label("Mash Efficiency (%)")
                yield Input(id="mash-efficiency", value="75")

            with Vertical(id="right-pane"):
                yield Static("═══ Style Selector ═══", id="style-header")
                yield Input(id="style-filter", placeholder="Filter styles...")
                yield ListView(id="style-list")
                yield Static(id="style-info")

                yield Static("═══ Settings ═══", id="settings-header")
                yield Label("Theme")
                yield Select([], id="theme-select", prompt="Select theme...")
                yield Button("New Recipe", id="btn-new-recipe")
                yield Button("Brew Wizard", id="btn-wizard", variant="primary")
                yield Button("Save As...", id="btn-save-as", variant="primary")
                yield Button("Open...", id="btn-open")
                yield Button("Build Inventory", id="btn-inventory", variant="primary")
                yield Button("Edit Inventory", id="btn-edit-inventory")

                yield Static("═══ Dashboard ═══", id="dashboard-header")
                yield Static("OG:  —", id="og-display")
                yield GaugeBar(id="og-gauge")
                yield Static("SRM: —", id="srm-display")
                yield GaugeBar(id="srm-gauge")
                yield Static("IBU: —", id="ibu-display")
                yield GaugeBar(id="ibu-gauge")
                yield Static("FG:  —", id="fg-display")
                yield GaugeBar(id="fg-gauge")
                yield Static("ABV: —", id="abv-display")
                yield GaugeBar(id="abv-gauge")

        yield Footer()

    def on_mount(self) -> None:
        self._all_styles = load_styles()
        self._populate_style_list(self._all_styles)
        for gauge_id in (
            "#og-gauge",
            "#srm-gauge",
            "#ibu-gauge",
            "#fg-gauge",
            "#abv-gauge",
        ):
            self.query_one(gauge_id, GaugeBar).display = False

        self._inventory = Inventory.load(inventory_path(Path(self._config.recipe_path)))
        if (
            not self._inventory.nonempty
            and inventory_path(Path(self._config.recipe_path)).exists()
        ):
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

        # Unit labels and defaults
        self._update_unit_labels()
        if self._imperial():
            self.batch_size_l = gal_to_l(5.0)
            self.query_one("#batch-size", Input).value = "5.0"

        self._malt_additions = [
            MaltAddition(
                "Pale 2-Row", lb_to_kg(11.0) if self._imperial() else 5.0, 2.0, 37.0
            ),
        ]
        self._rebuild_malt_ui()

        self._painted = True
        self._recalc()

    def _update_unit_labels(self) -> None:
        label = "gal" if self._imperial() else "L"
        self.query_one("#batch-size-label", Label).update(f"Batch Size ({label})")

    @staticmethod
    def _is_valid_float(raw: str) -> bool:
        if raw is None:
            return False
        if isinstance(raw, str) and raw.strip() == "":
            return False
        try:
            float(raw)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def _require_recalc(self) -> None:
        if self._recalc_id:
            return
        self._recalc_id += 1
        try:
            self._recalc()
        finally:
            self._recalc_id -= 1

    # ── Dynamic UI builders ──────────────────────────────────────

    def _rebuild_malt_ui(self) -> None:
        container = self.query_one("#malt-additions", Vertical)
        container.remove_children()
        for a in self._malt_additions:
            container.mount(MaltRow(a, self._imperial()))

    def _rebuild_hop_ui(self) -> None:
        container = self.query_one("#hop-additions", Vertical)
        container.remove_children()
        for a in self._hop_additions:
            container.mount(HopRow(a, self._imperial()))

    # ── List population ──────────────────────────────────────────

    def _populate_style_list(self, styles: List[Style]) -> None:
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

    # ── Input handling ───────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        raw = event.value
        input_id = event.input.id

        # Text-search filters — no float validation needed
        if input_id in ("style-filter", "malt-filter", "hop-filter"):
            if input_id == "style-filter":
                self.style_query = raw
            elif input_id == "malt-filter":
                self.malt_query = raw
            elif input_id == "hop-filter":
                self.hop_query = raw
            return

        valid = self._is_valid_float(raw)
        event.input.set_class(not valid, "invalid")

        if not valid:
            return

        if input_id == "batch-size":
            raw_val = float(raw)
            batch_l = raw_val if not self._imperial() else gal_to_l(raw_val)
            self.batch_size_l = self._clamp(batch_l, 0.1, 200.0)
        elif input_id == "fg-estimate":
            self.fg_estimate = self._clamp(float(raw), 0.990, 1.200)
        elif input_id == "mash-efficiency":
            self.mash_efficiency_pct = self._clamp(float(raw), 1.0, 100.0)
        elif input_id and input_id.startswith("malt-wt-"):
            uid = int(input_id.split("-")[-1])
            raw_lb_or_kg = float(raw)
            weight_kg = lb_to_kg(raw_lb_or_kg) if self._imperial() else raw_lb_or_kg
            weight_kg = self._clamp(weight_kg, 0.0, 100.0)
            for a in self._malt_additions:
                if a.uid == uid:
                    a.weight_kg = weight_kg
                    break
            self._require_recalc()
        elif input_id and input_id.startswith("hop-wt-"):
            uid = int(input_id.split("-")[-1])
            raw_oz_or_g = float(raw)
            weight_g = oz_to_g(raw_oz_or_g) if self._imperial() else raw_oz_or_g
            weight_g = self._clamp(weight_g, 0.0, 5000.0)
            for a in self._hop_additions:
                if a.uid == uid:
                    a.weight_g = weight_g
                    break
            self._require_recalc()
        elif input_id and input_id.startswith("hop-time-"):
            uid = int(input_id.split("-")[-1])
            t = self._clamp(float(raw), 0.0, 180.0)
            for a in self._hop_additions:
                if a.uid == uid:
                    a.boil_time_min = t
                    break
            self._require_recalc()

    # ── ListView selection ───────────────────────────────────────

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
                weight_kg = lb_to_kg(1.0) if self._imperial() else 1.0
                addition = MaltAddition(
                    name=malt.name,
                    weight_kg=weight_kg,
                    lovibond=malt.lovibond,
                    ppg=malt.ppg,
                )
                uid = addition.uid
                self._malt_additions.append(addition)
                self._rebuild_malt_ui()
                self.malt_query = ""
                self.query_one("#malt-filter", Input).value = ""
                self.set_timer(
                    0.01,
                    lambda uid=uid: self.query_one(f"#malt-wt-{uid}", Input).focus(),
                )
                self._require_recalc()

        elif lv.id == "hop-list":
            matches = search_hops(self._all_hops, self.hop_query)
            if lv.index < len(matches):
                hop = matches[lv.index]
                weight_g = oz_to_g(1.0) if self._imperial() else 30.0
                addition = HopAddition(
                    name=hop.name,
                    weight_g=weight_g,
                    alpha_acid_pct=hop.alpha_acid_pct,
                    boil_time_min=60.0,
                )
                uid = addition.uid
                self._hop_additions.append(addition)
                self._rebuild_hop_ui()
                self.hop_query = ""
                self.query_one("#hop-filter", Input).value = ""
                self.set_timer(
                    0.01,
                    lambda uid=uid: self.query_one(f"#hop-wt-{uid}", Input).focus(),
                )
                self._require_recalc()

    # ── Ingredient watchers ──────────────────────────────────────

    def watch_style_query(self, query: str) -> None:
        if not self._painted:
            return
        matches = search_styles(self._all_styles, query)
        self._populate_style_list(matches)

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

    # ── Button / action handlers ─────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id and btn_id.startswith("malt-rm-"):
            uid = int(btn_id.split("-")[-1])
            self._malt_additions = [a for a in self._malt_additions if a.uid != uid]
            self._rebuild_malt_ui()
            self._require_recalc()
            self.query_one("#malt-filter", Input).focus()

        elif btn_id and btn_id.startswith("hop-rm-"):
            uid = int(btn_id.split("-")[-1])
            self._hop_additions = [a for a in self._hop_additions if a.uid != uid]
            self._rebuild_hop_ui()
            self._require_recalc()
            self.query_one("#hop-filter", Input).focus()

        elif btn_id == "btn-inventory":
            self.action_open_inventory()

        elif btn_id == "btn-edit-inventory":
            self.action_edit_inventory()

        elif btn_id == "btn-new-recipe":
            self.action_new_recipe()

        elif btn_id == "btn-save-as":
            self.action_save_recipe_as()

        elif btn_id == "btn-wizard":
            self.action_open_wizard()

        elif btn_id == "btn-open":
            self.action_open_recipe()

    def action_open_inventory(self) -> None:
        self.push_screen(
            InventoryScreen(self._config.recipe_path, imperial=self._imperial()),
            self._on_inventory_closed,
        )

    def action_open_wizard(self) -> None:
        self.push_screen(
            RecipeWizardScreen(
                self._all_styles,
                self._all_malts,
                self._all_hops,
                imperial=self._imperial(),
            ),
            self._on_wizard_done,
        )

    def action_focus_style_filter(self) -> None:
        self.query_one("#style-filter", Input).focus()

    def action_edit_inventory(self) -> None:
        self.push_screen(
            InventoryEditScreen(self._config.recipe_path),
            self._on_inventory_edit_closed,
        )

    def action_toggle_units(self) -> None:
        if self._imperial():
            self._config.unit_system = UnitSystem.METRIC
        else:
            self._config.unit_system = UnitSystem.IMPERIAL
        self._config.save()
        self._update_unit_labels()

        # Convert batch-size input in place
        batch_input = self.query_one("#batch-size", Input)
        if self._imperial():
            batch_input.value = f"{l_to_gal(self.batch_size_l):.1f}"
        else:
            batch_input.value = f"{self.batch_size_l:.1f}"

        self._rebuild_malt_ui()
        self._rebuild_hop_ui()
        self.notify(f"Units: {self._config.unit_system}", timeout=2)

    def _on_inventory_edit_closed(self, _result: object = None) -> None:
        inv_path = inventory_path(Path(self._config.recipe_path))
        self._inventory = Inventory.load(inv_path)
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

    def _on_inventory_closed(self, _result: object = None) -> None:
        inv_path = inventory_path(Path(self._config.recipe_path))
        self._inventory = Inventory.load(inv_path)
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

    def _on_wizard_done(self, result: WizardResult | None = None) -> None:
        if result is None:
            return
        self._malt_additions.clear()
        self._hop_additions.clear()
        MaltAddition.__next_uid = 0
        HopAddition.__next_uid = 0

        self.batch_size_l = result.batch_size_l
        if self._imperial():
            self.query_one("#batch-size", Input).value = (
                f"{l_to_gal(result.batch_size_l):.1f}"
            )
        else:
            self.query_one("#batch-size", Input).value = f"{result.batch_size_l:.1f}"

        for d in result.malt_additions:
            self._malt_additions.append(MaltAddition(**d))
        for d in result.hop_additions:
            self._hop_additions.append(HopAddition(**d))

        if result.style_name:
            for s in self._all_styles:
                if s.name == result.style_name:
                    self.selected_style = s
                    self.query_one("#style-filter", Input).value = result.style_name
                    break

        self._recipe_style_name = result.style_name
        self._recipe_yeast = result.yeast
        self._recipe_pitching_temp = result.pitching_temp
        self._recipe_fermentation_time = result.fermentation_time
        self._recipe_notes = result.notes

        self._rebuild_malt_ui()
        self._rebuild_hop_ui()
        self._require_recalc()
        if self._malt_additions:
            self.query_one(f"#malt-wt-{self._malt_additions[0].uid}", Input).focus()
        else:
            self.query_one("#batch-size", Input).focus()
        self.notify("Recipe created from wizard!", timeout=3)

    def action_new_recipe(self) -> None:
        self._malt_additions.clear()
        self._hop_additions.clear()
        self._current_recipe_name = None
        if self._imperial():
            self.batch_size_l = gal_to_l(5.0)
            self.query_one("#batch-size", Input).value = "5.0"
        else:
            self.batch_size_l = 20.0
            self.query_one("#batch-size", Input).value = "20.0"
        self.fg_estimate = 1.010
        self.mash_efficiency_pct = 75.0
        self.selected_style = None
        self._recipe_style_name = None
        self._recipe_yeast = None
        self._recipe_pitching_temp = None
        self._recipe_fermentation_time = None
        self._recipe_notes = None
        self.query_one("#fg-estimate", Input).value = "1.010"
        self.query_one("#mash-efficiency", Input).value = "75"
        self._rebuild_malt_ui()
        self._rebuild_hop_ui()
        self._require_recalc()
        self.query_one("#batch-size", Input).focus()
        self.notify("New recipe started", timeout=3)

    def action_save_recipe_as(self) -> None:
        self.push_screen(
            SaveAsScreen(self._config.recipe_path, self._current_recipe_name),
            self._on_save_name,
        )

    def _on_save_name(self, name: str | None) -> None:
        if name is None:
            return
        self._current_recipe_name = name
        recipe = self._build_recipe_dict()
        path = Path(self._config.recipe_path) / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(recipe, f, indent=2)
        self.notify(f"Saved: {name}", timeout=3)

    def action_open_recipe(self) -> None:
        self.push_screen(
            OpenRecipeScreen(self._config.recipe_path),
            self._on_open_name,
        )

    def _on_open_name(self, name: str | None) -> None:
        if name is None:
            return
        path = Path(self._config.recipe_path) / f"{name}.json"
        if not path.is_file():
            self.notify(f"Recipe not found: {name}", severity="warning", timeout=3)
            return
        with open(path) as f:
            recipe = json.load(f)

        MaltAddition.__next_uid = 0
        HopAddition.__next_uid = 0

        self._current_recipe_name = name
        self.batch_size_l = recipe.get("batch_size_l", 20.0)
        self.fg_estimate = recipe.get("fg_estimate", 1.010)
        self.mash_efficiency_pct = recipe.get("mash_efficiency_pct", 75.0)
        self._recipe_style_name = recipe.get("style_name")
        self._recipe_yeast = recipe.get("yeast")
        self._recipe_pitching_temp = recipe.get("pitching_temp")
        self._recipe_fermentation_time = recipe.get("fermentation_time")
        self._recipe_notes = recipe.get("notes")
        self._malt_additions = [
            MaltAddition(**a) for a in recipe.get("malt_additions", [])
        ]
        self._hop_additions = [
            HopAddition(**a) for a in recipe.get("hop_additions", [])
        ]

        # Set input values in display units
        if self._imperial():
            self.query_one("#batch-size", Input).value = (
                f"{l_to_gal(self.batch_size_l):.1f}"
            )
        else:
            self.query_one("#batch-size", Input).value = str(self.batch_size_l)
        self.query_one("#fg-estimate", Input).value = str(self.fg_estimate)
        self.query_one("#mash-efficiency", Input).value = str(self.mash_efficiency_pct)
        self._rebuild_malt_ui()
        self._rebuild_hop_ui()
        self._require_recalc()
        self.query_one("#batch-size", Input).focus()
        self.notify(f"Loaded: {name}", timeout=3)

    def _build_recipe_dict(self) -> dict:
        return {
            "version": 3,
            "unit_system": self._config.unit_system,
            "batch_size_l": self.batch_size_l,
            "fg_estimate": self.fg_estimate,
            "mash_efficiency_pct": self.mash_efficiency_pct,
            "style_name": self._recipe_style_name,
            "yeast": self._recipe_yeast,
            "pitching_temp": self._recipe_pitching_temp,
            "fermentation_time": self._recipe_fermentation_time,
            "notes": self._recipe_notes,
            "malt_additions": [
                {
                    "name": a.name,
                    "weight_kg": a.weight_kg,
                    "lovibond": a.lovibond,
                    "ppg": a.ppg,
                }
                for a in self._malt_additions
            ],
            "hop_additions": [
                {
                    "name": a.name,
                    "weight_g": a.weight_g,
                    "alpha_acid_pct": a.alpha_acid_pct,
                    "boil_time_min": a.boil_time_min,
                }
                for a in self._hop_additions
            ],
        }

    # ── Theme ────────────────────────────────────────────────────

    def action_focus_theme(self) -> None:
        self.query_one("#theme-select", Select).focus()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "theme-select":
            self.theme = str(event.value)
            self._config.theme = str(event.value)
            self._config.save()
            self.notify(f"Theme: {str(event.value)}", timeout=3)

    @property
    def recipe_path(self) -> str:
        return self._config.recipe_path

    # ── Reactive watchers ────────────────────────────────────────

    def watch_selected_style(self, style: Optional[Style]) -> None:
        if not self._painted:
            return
        self._update_style_info(style)
        self._update_gauge_targets(style)
        self._refresh_all_displays()

    def _on_input_reactive_changed(self, _value: float) -> None:
        if self._painted:
            self._require_recalc()

    watch_batch_size_l = _on_input_reactive_changed
    watch_mash_efficiency_pct = _on_input_reactive_changed

    def watch_fg_estimate(self, value: float) -> None:
        if not self._painted:
            return
        self._require_recalc()
        self._refresh_display("fg-display", "FG", value, ".3f")
        if self.selected_style:
            self.query_one("#fg-gauge", GaugeBar).value = value

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

    def watch_abv(self, value: float) -> None:
        if self._painted:
            self._refresh_display("abv-display", "ABV", value, ".2f")
            if self.selected_style:
                self.query_one("#abv-gauge", GaugeBar).value = value

    # ── Display helpers ──────────────────────────────────────────

    _WIDGET_MAP = [
        ("og-display", "OG", "og", ".4f"),
        ("srm-display", "SRM", "srm", ".2f"),
        ("ibu-display", "IBU", "ibu", ".1f"),
        ("fg-display", "FG", "fg_estimate", ".3f"),
        ("abv-display", "ABV", "abv", ".2f"),
    ]

    def _refresh_display(
        self,
        widget_id: str,
        label: str,
        value: float,
        fmt: str,
    ) -> None:
        style = self.selected_style
        w = self.query_one(f"#{widget_id}", Static)
        if style is None:
            w.update(f"{label}: {value:{fmt}}")
            return

        prefix = widget_id.split("-")[0]
        lo = getattr(style, f"{prefix}_min")
        hi = getattr(style, f"{prefix}_max")

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
            f"FG {style.fg_range_str()}  "
            f"ABV {style.abv_range_str()}"
        )

    def _update_gauge_targets(self, style: Optional[Style]) -> None:
        if style is None:
            for gid in (
                "#og-gauge",
                "#srm-gauge",
                "#ibu-gauge",
                "#fg-gauge",
                "#abv-gauge",
            ):
                self.query_one(gid, GaugeBar).display = False
            return

        for prefix in ("og", "srm", "ibu", "fg", "abv"):
            g = self.query_one(f"#{prefix}-gauge", GaugeBar)
            g.display = True
            g.value = self._gauge_value(prefix)
            g.minimum = getattr(style, f"{prefix}_min")
            g.maximum = getattr(style, f"{prefix}_max")

    def _gauge_value(self, prefix: str) -> float:
        mapping = {
            "og": self.og,
            "srm": self.srm,
            "ibu": self.ibu,
            "fg": self.fg_estimate,
            "abv": self.abv,
        }
        return mapping[prefix]

    def _refresh_all_displays(self) -> None:
        for wid, label, attr, fmt in self._WIDGET_MAP:
            self._refresh_display(wid, label, getattr(self, attr), fmt)

    # ── Calculation ──────────────────────────────────────────────

    def _recalc(self) -> None:
        malt_weights = [a.weight_kg for a in self._malt_additions]
        malt_ppgs = [a.ppg for a in self._malt_additions]
        malt_lovis = [a.lovibond for a in self._malt_additions]
        efficiency = self.mash_efficiency_pct / 100.0

        self.og = calculate_og(
            malt_weights,
            self.batch_size_l,
            efficiency,
            malt_ppgs,
        )
        self.srm = calculate_srm(malt_weights, malt_lovis, self.batch_size_l)

        hop_data = [
            (a.weight_g, a.alpha_acid_pct, a.boil_time_min) for a in self._hop_additions
        ]
        self.ibu = calculate_ibu_multi(hop_data, self.batch_size_l, self.og)

        self.abv = calculate_abv(self.og, self.fg_estimate)
