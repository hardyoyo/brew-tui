"""Tests for the conversational recipe wizard screen."""

import pytest
from textual.widgets import Input, RichLog

from brew_tui.app import BrewTUI
from brew_tui.recipe_wizard_screen import RecipeWizardScreen, WizardResult


@pytest.mark.asyncio
async def test_compose():
    """Screen renders expected widgets."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()
        assert screen.query_one("#conv-log", RichLog)
        assert screen.query_one("#conv-input", Input)


@pytest.mark.asyncio
async def test_first_stage_is_style():
    """First stage asks about style."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()
        assert screen._stage == 0
        assert screen._stages[0]["key"] == "style"


@pytest.mark.asyncio
async def test_skip_moves_to_next_stage():
    """Typing skip advances to the next stage."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()

        stage_before = screen._stage
        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        assert screen._stage == stage_before + 1


@pytest.mark.asyncio
async def test_back_returns_to_previous_stage():
    """Typing back returns to the previous stage after skip."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        stage_after_skip = screen._stage

        inp.value = "back"
        await inp.action_submit()
        await pilot.pause()
        assert screen._stage == stage_after_skip - 1


@pytest.mark.asyncio
async def test_style_parsing_fuzzy():
    """Fuzzy style matching works."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()
        inp = screen.query_one("#conv-input", Input)
        inp.value = "IPA"
        await inp.action_submit()
        await pilot.pause()
        assert screen._result.style_name is not None
        assert "IPA" in screen._result.style_name


@pytest.mark.asyncio
async def test_style_parsing_by_id():
    """Style ID matching works (e.g., '21B')."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        app.push_screen(screen)
        await pilot.pause()

        for s in app._all_styles:
            if s.style_id == "21B":
                inp = screen.query_one("#conv-input", Input)
                inp.value = "21B"
                await inp.action_submit()
                await pilot.pause()
                assert screen._result.style_name == s.name
                return


@pytest.mark.asyncio
async def test_batch_size_parsing_gallons():
    """Batch size in gallons is converted to liters."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=True
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "5 gal"
        await inp.action_submit()
        await pilot.pause()
        assert abs(screen._result.batch_size_l - 18.927) < 0.1


@pytest.mark.asyncio
async def test_batch_size_parsing_liters():
    """Batch size in liters."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "20 L"
        await inp.action_submit()
        await pilot.pause()
        assert abs(screen._result.batch_size_l - 20.0) < 0.1


@pytest.mark.asyncio
async def test_malt_parsing():
    """Malt entries are parsed and looked up."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "Pale 2-Row: 5 kg"
        await inp.action_submit()
        await pilot.pause()

        assert len(screen._result.malt_additions) == 1
        malt = screen._result.malt_additions[0]
        assert malt["name"] == "Pale 2-Row"
        assert abs(malt["weight_kg"] - 5.0) < 0.01
        assert malt["ppg"] == 37
        assert malt["lovibond"] == 3.6


@pytest.mark.asyncio
async def test_malt_parsing_unknown_name():
    """Unknown malt names get sensible defaults."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "Mystery Grain: 2 kg"
        await inp.action_submit()
        await pilot.pause()

        assert len(screen._result.malt_additions) == 1
        malt = screen._result.malt_additions[0]
        assert malt["name"] == "Mystery Grain"
        assert malt["ppg"] == 37
        assert malt["lovibond"] == 2


@pytest.mark.asyncio
async def test_malt_multiple_items():
    """Multiple comma-separated malts."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "Pale 2-Row: 5 kg, Vienna: 1 kg"
        await inp.action_submit()
        await pilot.pause()

        assert len(screen._result.malt_additions) == 2


@pytest.mark.asyncio
async def test_hop_parsing_with_schedule():
    """Hop entries with boil time are parsed."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        for _ in range(4):
            inp.value = "skip"
            await inp.action_submit()
            await pilot.pause()

        inp.value = "Cascade: 30 g @ 60"
        await inp.action_submit()
        await pilot.pause()

        assert len(screen._result.hop_additions) == 1
        hop = screen._result.hop_additions[0]
        assert hop["name"] == "Cascade"
        assert abs(hop["weight_g"] - 30) < 0.1
        assert abs(hop["boil_time_min"] - 60) < 0.1


@pytest.mark.asyncio
async def test_hop_parsing_default_time():
    """Hop without schedule defaults to 60 min."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        for _ in range(4):
            inp.value = "skip"
            await inp.action_submit()
            await pilot.pause()

        inp.value = "Citra: 15 g"
        await inp.action_submit()
        await pilot.pause()

        assert len(screen._result.hop_additions) == 1
        assert screen._result.hop_additions[0]["boil_time_min"] == 60.0


@pytest.mark.asyncio
async def test_text_stages_store_raw():
    """Yeast, temp, time, notes store free text."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=False
        )
        app.push_screen(screen)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)
        for _ in range(5):
            inp.value = "skip"
            await inp.action_submit()
            await pilot.pause()

        inp.value = "US-05"
        await inp.action_submit()
        await pilot.pause()
        assert screen._result.yeast == "US-05"

        inp.value = "68 F"
        await inp.action_submit()
        await pilot.pause()
        assert screen._result.pitching_temp == "68 F"

        inp.value = "2 weeks"
        await inp.action_submit()
        await pilot.pause()
        assert screen._result.fermentation_time == "2 weeks"

        inp.value = "Dry hop with 2 oz"
        await inp.action_submit()
        await pilot.pause()
        assert screen._result.notes == "Dry hop with 2 oz"


@pytest.mark.asyncio
async def test_full_wizard_completes():
    """Completing all stages produces a WizardResult."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(
            app._all_styles, app._all_malts, app._all_hops, imperial=True
        )
        results = []
        app.push_screen(screen, results.append)
        await pilot.pause()

        inp = screen.query_one("#conv-input", Input)

        inp.value = "American IPA"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "5 gal"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "Pale 2-Row: 10 lbs"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "Crystal 40: 0.5 lbs"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "Cascade: 1 oz @ 60, Citra: 0.5 oz @ 5"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "US-05"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "68 F"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "2 weeks"
        await inp.action_submit()
        await pilot.pause()

        inp.value = "Dry hop with 2 oz Citra"
        await inp.action_submit()
        await pilot.pause()

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, WizardResult)
        assert result.style_name == "American IPA"
        assert abs(result.batch_size_l - 18.927) < 0.1
        assert len(result.malt_additions) == 2
        assert len(result.hop_additions) == 2
        assert result.yeast == "US-05"
        assert result.pitching_temp == "68 F"
        assert result.fermentation_time == "2 weeks"
        assert result.notes == "Dry hop with 2 oz Citra"


@pytest.mark.asyncio
async def test_dismiss_returns_none():
    """Pressing Esc returns None."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        screen = RecipeWizardScreen(app._all_styles, app._all_malts, app._all_hops)
        results = []
        app.push_screen(screen, results.append)
        await pilot.pause()

        screen.action_dismiss_wizard()
        await pilot.pause()

        assert len(results) == 1
        assert results[0] is None


@pytest.mark.asyncio
async def test_wizard_integration_with_app():
    """Wizard result populates the main app form."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        app.action_open_wizard()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, RecipeWizardScreen)

        inp = screen.query_one("#conv-input", Input)
        inp.value = "American IPA"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "5 gal"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "Pale 2-Row: 10 lbs"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "Cascade: 1 oz @ 60"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "US-05"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()
        inp.value = "skip"
        await inp.action_submit()
        await pilot.pause()

        assert len(app._malt_additions) == 1
        assert len(app._hop_additions) == 1
        assert app._recipe_yeast == "US-05"
        assert app._recipe_style_name == "American IPA"
