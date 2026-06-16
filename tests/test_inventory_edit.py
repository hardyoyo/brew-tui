"""Tests for InventoryEditScreen."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from textual.widgets import Button, Label

from brew_tui.app import BrewTUI
from brew_tui.inventory import INVENTORY_FILENAME, HopItem, Inventory, MaltItem
from brew_tui.inventory_edit_screen import InventoryEditScreen


@pytest.mark.asyncio
async def test_edit_screen_empty():
    """Screen shows 'no items' when inventory is empty."""
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / INVENTORY_FILENAME
        Inventory().save(path)
        app = BrewTUI()
        async with app.run_test(headless=True, size=(80, 24)) as pilot:
            await pilot.pause()
            screen = InventoryEditScreen(tmp)
            app.push_screen(screen)
            await pilot.pause()
            empty = screen.query("#ei-empty")
            assert len(empty) == 1


@pytest.mark.asyncio
async def test_edit_screen_shows_items():
    """Screen shows inventory items grouped by category."""
    with TemporaryDirectory() as tmp:
        inv = Inventory(
            malts=[MaltItem("Pale 2-Row", 5.0)],
            hops=[HopItem("Cascade", 50.0)],
        )
        path = Path(tmp) / INVENTORY_FILENAME
        inv.save(path)
        app = BrewTUI()
        async with app.run_test(headless=True, size=(80, 24)) as pilot:
            await pilot.pause()
            screen = InventoryEditScreen(tmp)
            app.push_screen(screen)
            await pilot.pause()
            labels = [str(w.render()) for w in screen.query(Label)]
            combined = " ".join(labels)
            assert "Pale 2-Row" in combined
            assert "Cascade" in combined


@pytest.mark.asyncio
async def test_edit_screen_remove_item():
    """Clicking remove on an item deletes it from inventory."""
    with TemporaryDirectory() as tmp:
        inv = Inventory(
            malts=[MaltItem("Pale 2-Row", 5.0), MaltItem("Munich", 1.0)],
        )
        path = Path(tmp) / INVENTORY_FILENAME
        inv.save(path)
        app = BrewTUI()
        async with app.run_test(headless=True, size=(80, 24)) as pilot:
            await pilot.pause()
            screen = InventoryEditScreen(tmp)
            app.push_screen(screen)
            await pilot.pause()
            rm_btn = screen.query_one("#ei-rm-malts-0", Button)
            rm_btn.press()
            await pilot.pause()
            labels = [str(w.render()) for w in screen.query(Label)]
            combined = " ".join(labels)
            assert "Pale 2-Row" not in combined
            assert "Munich" in combined
            loaded = Inventory.load(path)
            assert len(loaded.malts) == 1
            assert loaded.malts[0].name == "Munich"


@pytest.mark.asyncio
async def test_edit_screen_delete_all():
    """Delete All button clears the inventory."""
    with TemporaryDirectory() as tmp:
        inv = Inventory(malts=[MaltItem("Pale 2-Row", 5.0)])
        path = Path(tmp) / INVENTORY_FILENAME
        inv.save(path)
        app = BrewTUI()
        async with app.run_test(headless=True, size=(80, 24)) as pilot:
            await pilot.pause()
            screen = InventoryEditScreen(tmp)
            app.push_screen(screen)
            await pilot.pause()
            screen.query_one("#ei-delete-all", Button).press()
            await pilot.pause()
            empty = screen.query("#ei-empty")
            assert len(empty) == 1
            loaded = Inventory.load(path)
            assert not loaded.nonempty
