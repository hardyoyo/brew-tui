"""Screens for saving and loading named recipes."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView


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
            id="sas-input",
            placeholder="Recipe name...",
        )
        with Horizontal(id="sas-btns"):
            yield Button("Save", id="sas-save", variant="primary")
            yield Button("Cancel", id="sas-cancel")

    def on_mount(self) -> None:
        self.query_one("#sas-input", Input).focus()

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
    """List saved recipes to load or delete."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, recipe_dir: str):
        super().__init__()
        self._recipe_dir = recipe_dir

    def compose(self) -> ComposeResult:
        yield Label("Select a recipe to open:", id="ors-prompt")
        yield ListView(id="ors-list")
        yield Button("Cancel", id="ors-cancel")

    def on_mount(self) -> None:
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        lv = self.query_one("#ors-list", ListView)
        lv.clear()
        for name in recipe_files(self._recipe_dir):
            lv.append(
                ListItem(
                    Label(name, id=f"ors-item-{name}"),
                )
            )
        if lv.children:
            lv.index = 0
        else:
            lv.append(ListItem(Label("(no saved recipes)")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv = event.list_view
        if lv.index is None:
            return
        names = recipe_files(self._recipe_dir)
        if lv.index < len(names):
            self.dismiss(names[lv.index])

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
