"""Conversational inventory-builder screen."""

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from .inventory import (
    INVENTORY_FILENAME,
    STAGE_DONE,
    STAGE_WELCOME,
    _build_stages,
    Inventory,
)


class InventoryScreen(Screen):
    """Conversational wizard for building ingredient inventory."""

    BINDINGS = [
        ("escape", "dismiss_inventory", "Return"),
    ]

    def __init__(self, recipe_dir: str | None = None, imperial: bool = False):
        super().__init__()
        self._recipe_dir = recipe_dir or str(Path.home() / ".brew-tui-recipes")
        self._inventory_file = Path(self._recipe_dir) / INVENTORY_FILENAME
        self._stages = _build_stages(imperial)

    def compose(self) -> ComposeResult:
        yield Header("Build Inventory")
        yield RichLog(id="conv-log", highlight=True, markup=True, wrap=True)
        yield Input(id="conv-input", placeholder="Type your answer here...")
        yield Footer()

    def on_mount(self) -> None:
        self._inventory: Inventory = Inventory.load(self._inventory_file)
        self._stage = -1
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write("[bold yellow]Brewer[/]  " + STAGE_WELCOME)
        self._next_stage()

    def action_dismiss_inventory(self) -> None:
        self.dismiss(True)

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
        self._inventory.save(self._inventory_file)
        self.app.notify("Inventory saved!", timeout=4)
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write("[bold yellow]Brewer[/]  " + STAGE_DONE)
        inp = self.query_one("#conv-input", Input)
        inp.disabled = True
        inp.placeholder = "Inventory saved — press Esc to return"

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
        items = stage["parser"](text)
        if not items:
            log.write(
                "[bold yellow]Brewer[/]  "
                "Hmm, I couldn't read that. Try [bold]name[/] or [bold]name:amount[/] "
                "separated by commas, or type [bold]skip[/]."
            )
            inp.focus()
            return

        target = getattr(self._inventory, stage["key"])
        target.extend(items)
        names = ", ".join(f"[bold]{i.name}[/]" for i in items)
        log.write("[bold yellow]Brewer[/]  " + stage["confirm"].format(names))
        self._next_stage()
