"""Conversational inventory-builder screen.

Walks the user through building their ingredient inventory
with friendly prompts and parsing.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from .inventory import (
    INVENTORY_FILENAME,
    STAGES,
    STAGE_DONE,
    STAGE_WELCOME,
    Inventory,
)

INVENTORY_FILE = Path.home() / ".brew-tui-recipes" / INVENTORY_FILENAME


class InventoryScreen(Screen):
    """Conversational wizard for building ingredient inventory."""

    def compose(self) -> ComposeResult:
        yield Header("Build Inventory")
        yield RichLog(id="conv-log", highlight=True, markup=True, wrap=True)
        yield Input(id="conv-input", placeholder="Type your answer here...")
        yield Footer()

    def on_mount(self) -> None:
        self._inventory: Inventory = Inventory.load(INVENTORY_FILE)
        self._stage = -1
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write("[bold yellow]Brewer[/]  " + STAGE_WELCOME)
        self._next_stage()

    def _next_stage(self) -> None:
        self._stage += 1
        if self._stage >= len(STAGES):
            self._finish()
            return
        stage = STAGES[self._stage]
        log = self.query_one("#conv-log", RichLog)
        log.write("")
        log.write(f"[bold yellow]Brewer[/]  Let's talk [bold]{stage['title']}[/]!")
        log.write("[bold yellow]Brewer[/]  " + stage["prompt"])
        inp = self.query_one("#conv-input", Input)
        inp.clear()
        inp.focus()

    def _finish(self) -> None:
        self._inventory.save(INVENTORY_FILE)
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

        if self._stage >= len(STAGES):
            return

        if text.lower() in ("skip", "done", "none", "pass", ""):
            log.write("[bold yellow]Brewer[/]  No problem! Moving on...")
            self._next_stage()
            return

        stage = STAGES[self._stage]
        items = stage["parser"](text)
        if not items:
            log.write(
                "[bold yellow]Brewer[/]  "
                "Hmm, I couldn't read that. Try [bold]name:amount[/] "
                "format separated by commas, or type [bold]skip[/]."
            )
            inp.focus()
            return

        target = getattr(self._inventory, stage["key"])
        target.extend(items)
        names = ", ".join(f"[bold]{i.name}[/]" for i in items)
        log.write("[bold yellow]Brewer[/]  " + stage["confirm"].format(names))
        self._next_stage()
