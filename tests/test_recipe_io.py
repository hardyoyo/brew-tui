"""Tests for recipe save/load screens and helpers."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from textual.widgets import Button, Input, ListView

from brew_tui.app import BrewTUI, MaltAddition
from brew_tui.recipe_io_screen import (
    _sanitize,
    recipe_files,
    SaveAsScreen,
    OpenRecipeScreen,
)


def test_sanitize():
    assert _sanitize("My IPA") == "My_IPA"
    assert _sanitize("   ") == "unnamed"
    assert _sanitize("hello world") == "hello_world"
    assert _sanitize("foo/bar:baz") == "foo_bar_baz"


def test_recipe_files(tmp_path: Path):
    d = tmp_path / "recipes"
    d.mkdir()
    (d / "My IPA.json").write_text("{}")
    (d / "Stout.json").write_text("{}")
    (d / "inventory.json").write_text("{}")
    names = recipe_files(str(d))
    assert "My IPA" in names
    assert "Stout" in names
    assert "inventory" not in names


def test_recipe_files_empty():
    assert recipe_files("/nonexistent_path_xyz") == []


@pytest.mark.asyncio
async def test_save_as_screen_composes():
    app = BrewTUI()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.pause()
        screen = SaveAsScreen(app._config.recipe_path)
        app.push_screen(screen, lambda name: None)
        await pilot.pause()
        inp = screen.query_one("#sas-input", Input)
        assert inp is not None
        assert inp.placeholder == "Recipe name..."
        screen.dismiss(None)
        await pilot.pause()


@pytest.mark.asyncio
async def test_open_recipe_screen_empty():
    app = BrewTUI()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.pause()
        screen = OpenRecipeScreen(app._config.recipe_path)
        app.push_screen(screen, lambda name: None)
        await pilot.pause()
        lv = screen.query_one("#ors-list", ListView)
        assert len(lv.children) > 0
        screen.dismiss(None)
        await pilot.pause()


@pytest.mark.asyncio
async def test_save_and_load_named_recipe():
    app = BrewTUI()
    tmp = TemporaryDirectory()
    app._config.recipe_path = tmp.name
    app._config.save()
    async with app.run_test(headless=True, size=(120, 32)) as pilot:
        await pilot.pause()

        app._malt_additions = [
            MaltAddition("Pale 2-Row", 5.0, 2.0, 37.0),
        ]
        app._rebuild_malt_ui()
        app.batch_size_l = 25.0
        app.fg_estimate = 1.012
        app.mash_efficiency_pct = 70.0
        await pilot.pause()

        app.action_save_recipe_as()
        await pilot.pause()
        save_screen = app.screen
        save_screen.query_one("#sas-input", Input).value = "Test Recipe"
        save_screen.query_one("#sas-save", Button).press()
        await pilot.pause()

        path = Path(tmp.name) / "Test_Recipe.json"
        assert path.is_file()

        app.action_new_recipe()
        await pilot.pause()
        assert app.batch_size_l == 20.0

        app.action_open_recipe()
        await pilot.pause()
        open_screen = app.screen
        open_screen.query_one("#ors-list", ListView).action_select_cursor()
        await pilot.pause()

        assert app.batch_size_l == 25.0
        assert app.fg_estimate == 1.012
        assert app.mash_efficiency_pct == 70.0
        assert app._current_recipe_name == "Test_Recipe"

    tmp.cleanup()
