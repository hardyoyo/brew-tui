"""Integration / smoke tests for the Textual TUI app."""

import pytest
from textual.widgets import ListView, Static
from brew_tui.app import BrewTUI


def _text(widget: Static) -> str:
    return str(widget.render())


@pytest.mark.asyncio
async def test_app_compose_and_defaults():
    """App composes without error and shows default calculated values."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        og = app.query_one("#og-display", Static)
        srm = app.query_one("#srm-display", Static)
        ibu = app.query_one("#ibu-display", Static)

        assert "OG:" in _text(og)
        assert "SRM:" in _text(srm)
        assert "IBU:" in _text(ibu)
        assert "1." in _text(og)


@pytest.mark.asyncio
async def test_input_updates_results():
    """Changing batch size reactive recalculates OG display."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        og_display = app.query_one("#og-display", Static)
        original = _text(og_display)

        app.batch_size_l = 40.0
        await pilot.pause()

        updated = _text(og_display)
        assert updated != original
        assert "1.028" in updated or "1.029" in updated


@pytest.mark.asyncio
async def test_zero_batch_size_no_crash():
    """Setting batch to 0 triggers guard fallback, no crash."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        app.batch_size_l = 0.0
        await pilot.pause()

        og = app.query_one("#og-display", Static)
        assert "OG:" in _text(og)


@pytest.mark.asyncio
async def test_empty_input_no_crash():
    """Zero malt + zero batch uses fallback, no crash."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        app.base_malt_kg = 0.0
        app.batch_size_l = 0.0
        await pilot.pause()

        og = app.query_one("#og-display", Static)
        assert "OG:" in _text(og)


@pytest.mark.asyncio
async def test_header_footer_present():
    """Header and Footer widgets render."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert app.query_one("Header") is not None
        assert app.query_one("Footer") is not None


@pytest.mark.asyncio
async def test_style_list_populated():
    """Style list is populated on mount."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#style-list", ListView)
        assert len(lv.children) > 0


@pytest.mark.asyncio
async def test_style_filter_narrows_list():
    """Filtering by text narrows the style list."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#style-list", ListView)
        initial = len(lv.children)

        app.style_query = "IPA"
        await pilot.pause()

        filtered = len(lv.children)
        assert filtered < initial
        assert filtered > 0


@pytest.mark.asyncio
async def test_select_style_shows_info():
    """Selecting a style displays its info."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert app._all_styles

        app.selected_style = app._all_styles[0]
        await pilot.pause()

        info = app.query_one("#style-info", Static)
        rendered = _text(info)
        assert app._all_styles[0].name in rendered


@pytest.mark.asyncio
async def test_select_style_shows_gauges():
    """Selecting a style makes gauges visible; deselecting hides them."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        og_g = app.query_one("#og-gauge")
        assert not og_g.display

        app.selected_style = app._all_styles[0]
        await pilot.pause()
        assert og_g.display

        app.selected_style = None
        await pilot.pause()
        assert not og_g.display


@pytest.mark.asyncio
async def test_select_style_shows_range_in_display():
    """Selecting a style shows range/status in the display statics."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        og_dis = app.query_one("#og-display", Static)
        # No style — no range info
        assert "within" not in _text(og_dis)

        app.selected_style = app._all_styles[0]
        await pilot.pause()
        rendered = _text(og_dis)
        assert "within" in rendered or "below" in rendered or "above" in rendered
