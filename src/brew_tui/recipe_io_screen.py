"""Screens for saving and loading named recipes."""

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static


def _sanitize(name: str) -> str:
    clean = "".join(c if c.isalnum() or c in "-_." else "_" for c in name.strip())
    return clean or "unnamed"


def recipe_files(recipe_dir: str) -> list[str]:
    """Return sorted recipe names (sans .json) in the recipe directory."""
    d = Path(recipe_dir)
    if not d.is_dir():
        return []
    names = []
    for p in sorted(d.iterdir()):
        if p.suffix == ".json" and p.stem not in ("inventory",):
            names.append(p.stem)
    return names


def _load_recipe_meta(recipe_dir: str, name: str) -> dict:
    path = Path(recipe_dir) / f"{name}.json"
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _format_preview(data: dict, fallback_name: str = "Unnamed") -> str:
    lines = []
    name = data.get("name") or fallback_name
    style = data.get("style_name") or "No style"
    batch = data.get("batch_size_l", 0)
    lines.append(f"[b]{name}[/b]")
    lines.append(f"Style: {style}")
    lines.append(f"Batch: {batch:.1f} L ({batch * 0.264:.1f} gal)")
    og = data.get("og")
    if og:
        lines.append(f"OG: {og:.4f}")
    fg = data.get("fg_estimate")
    if fg:
        lines.append(f"FG: {fg:.3f}")
    srm = data.get("srm")
    if srm:
        lines.append(f"SRM: {srm:.1f}")
    ibu = data.get("ibu")
    if ibu:
        lines.append(f"IBU: {ibu:.1f}")
    abv = data.get("abv")
    if abv:
        lines.append(f"ABV: {abv:.1f}%")
    malts = data.get("malt_additions", [])
    if malts:
        lines.append(f"\nMalts ({len(malts)}):")
        for m in malts:
            wt = m.get("weight_kg", 0)
            lines.append(f"  {m['name']} — {wt:.2f} kg ({wt * 2.205:.1f} lb)")
    hops = data.get("hop_additions", [])
    if hops:
        lines.append(f"\nHops ({len(hops)}):")
        for h in hops:
            wt = h.get("weight_g", 0)
            lines.append(
                f"  {h['name']} — {wt:.0f} g @ {h.get('boil_time_min', 0)} min"
            )
    yeast = data.get("yeast")
    if yeast:
        lines.append(f"\nYeast: {yeast}")
    notes = data.get("notes")
    if notes:
        lines.append(f"\nNotes: {notes}")
    return "\n".join(lines)


class SaveAsScreen(ModalScreen[str | None]):
    """Prompt for a recipe name to save."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, recipe_dir: str, current_name: str | None = None):
        super().__init__()
        self._recipe_dir = recipe_dir
        self._current_name = current_name or ""

    def compose(self) -> ComposeResult:
        yield Label("Save recipe as:", id="sas-prompt")
        yield Input(
            value=self._current_name,
            placeholder='e.g. "New Year Porter" → NewYearPorter.json',
            id="sas-input",
        )
        yield Static(id="sas-hint")
        with Horizontal(id="sas-btns"):
            yield Button("Save", id="sas-save", variant="primary")
            yield Button("Cancel", id="sas-cancel")

    def on_mount(self) -> None:
        inp = self.query_one("#sas-input", Input)
        inp.focus()
        preview = _sanitize(inp.value) or "unnamed"
        self.query_one("#sas-hint", Static).update(f"→ {preview}.json")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "sas-input":
            preview = _sanitize(event.input.value) or "unnamed"
            self.query_one("#sas-hint", Static).update(f"→ {preview}.json")

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self._do_save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sas-save":
            self._do_save()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _do_save(self) -> None:
        name = self.query_one("#sas-input", Input).value.strip()
        if not name:
            self.app.notify("Name cannot be empty", severity="warning", timeout=3)
            return
        name = _sanitize(name)
        self.dismiss(name)


class OpenRecipeScreen(ModalScreen[str | None]):
    """List saved recipes — preview details as you navigate."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, recipe_dir: str):
        super().__init__()
        self._recipe_dir = recipe_dir
        self._names: list[str] = []

    def compose(self) -> ComposeResult:
        yield Label("Select a recipe to open:", id="ors-prompt")
        with Horizontal(id="ors-body"):
            with Vertical(id="ors-list-col"):
                yield ListView(id="ors-list")
            with Vertical(id="ors-preview-col"):
                yield Static(id="ors-preview")
        yield Button("Cancel", id="ors-cancel")

    def on_mount(self) -> None:
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        self._names = recipe_files(self._recipe_dir)
        lv = self.query_one("#ors-list", ListView)
        lv.clear()
        for name in self._names:
            meta = _load_recipe_meta(self._recipe_dir, name)
            style = meta.get("style_name", "")
            label = f"{name}" + (f"  —  {style}" if style else "")
            lv.append(
                ListItem(Label(label)),
            )
        if lv.children:
            lv.index = 0
        else:
            lv.append(ListItem(Label("(no saved recipes)")))
            self.query_one("#ors-preview", Static).update("")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        lv = event.list_view
        if lv.index is None or lv.index >= len(self._names):
            return
        name = self._names[lv.index]
        meta = _load_recipe_meta(self._recipe_dir, name)
        preview = _format_preview(meta, fallback_name=name)
        self.query_one("#ors-preview", Static).update(preview)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv = event.list_view
        if lv.index is None:
            return
        if lv.index < len(self._names):
            self.dismiss(self._names[lv.index])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("ors-del-"):
            name = btn_id.removeprefix("ors-del-")
            path = Path(self._recipe_dir) / f"{name}.json"
            if path.is_file():
                path.unlink()
                self.app.notify(f"Deleted: {name}", timeout=3)
                self._rebuild_list()
            return
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
