"""Screen for viewing and editing stored inventory."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from .inventory import INVENTORY_FILENAME, Inventory


class _ItemRow(Horizontal):
    def __init__(self, label: str, btn_id: str) -> None:
        super().__init__(classes="ei-row")
        self._label = label
        self._btn_id = btn_id

    def compose(self) -> ComposeResult:
        yield Label(self._label, classes="ei-item-label")
        yield Button("✕", id=self._btn_id, classes="ei-rm-btn")


class InventoryEditScreen(Screen):
    BINDINGS = [
        ("escape", "dismiss_edit", "Return"),
    ]

    _CATEGORIES = [
        ("malts", "── Malts ──"),
        ("specialty_grains", "── Specialty Grains ──"),
        ("hops", "── Hops ──"),
        ("yeasts", "── Yeasts ──"),
    ]

    def __init__(self, recipe_dir: str | None = None):
        super().__init__()
        self._recipe_dir = recipe_dir or str(Path.home() / ".brew-tui-recipes")
        self._inventory_file = Path(self._recipe_dir) / INVENTORY_FILENAME
        self._inventory: Inventory = Inventory.load(self._inventory_file)
        self._btn_index: dict[str, tuple[str, int]] = {}

    def compose(self) -> ComposeResult:
        yield Header("Edit Inventory")
        with VerticalScroll(id="ei-scroll"):
            yield Label("Select items to remove, or delete all.", id="ei-intro")
            for attr, heading in self._CATEGORIES:
                yield Static(heading, classes="ei-section")
                yield Vertical(id=f"ei-{attr}")
            yield Button("Delete All", id="ei-delete-all", variant="error")
            yield Button("Done", id="ei-done", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild_all()

    def _rebuild_all(self) -> None:
        self._btn_index.clear()
        has_any = False
        for attr, _heading in self._CATEGORIES:
            container = self.query_one(f"#ei-{attr}", Vertical)
            container.remove_children()
            items = getattr(self._inventory, attr)
            for idx, item in enumerate(items):
                has_any = True
                if attr in ("malts", "specialty_grains"):
                    detail = f"{item.amount_kg} kg"
                elif attr == "hops":
                    detail = f"{item.amount_g} g"
                else:
                    detail = item.yeast_type
                btn_id = f"ei-rm-{attr}-{idx}"
                self._btn_index[btn_id] = (attr, item.name)
                container.mount(_ItemRow(f"{item.name}  ({detail})", btn_id))
        if not has_any:
            empty = self.query_one("#ei-scroll", VerticalScroll)
            if not empty.query("#ei-empty"):
                empty.mount(Label("No inventory items stored.", id="ei-empty"))

    def action_dismiss_edit(self) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "ei-done":
            self.dismiss(True)
            return

        if btn_id == "ei-delete-all":
            self._inventory = Inventory()
            self._save_and_show()
            return

        if btn_id and btn_id.startswith("ei-rm-"):
            info = self._btn_index.get(btn_id)
            if info is None:
                return
            attr, item_name = info
            items = getattr(self._inventory, attr)
            setattr(
                self._inventory,
                attr,
                [it for it in items if it.name != item_name],
            )
            self._save_and_show()

    def _save_and_show(self) -> None:
        self._inventory.save(self._inventory_file)
        self._rebuild_all()
        self.app.notify("Inventory updated", timeout=3)
