"""Integration / smoke tests for the Textual TUI app."""

import pytest
from textual.widgets import Input, ListView, Select, Static
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


@pytest.mark.asyncio
async def test_theme_selector_present():
    """Theme Select widget is populated on mount."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        ts = app.query_one("#theme-select", Select)
        assert len(ts._options) > 0


@pytest.mark.asyncio
async def test_theme_can_be_changed():
    """Changing the theme via Select updates app.theme."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        themes = sorted(app.available_themes)
        if len(themes) < 2:
            return
        new_theme = themes[1]
        app.theme = new_theme
        await pilot.pause()
        assert app.theme == new_theme


@pytest.mark.asyncio
async def test_recipe_path_default():
    """App exposes recipe_path from config."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert app.recipe_path is not None
        assert isinstance(app.recipe_path, str)


@pytest.mark.asyncio
async def test_malt_list_populated():
    """Malt inventory list is populated on mount."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#malt-list", ListView)
        assert len(lv.children) > 0


@pytest.mark.asyncio
async def test_hop_list_populated():
    """Hop inventory list is populated on mount."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#hop-list", ListView)
        assert len(lv.children) > 0


@pytest.mark.asyncio
async def test_malt_filter_narrows_list():
    """Filtering malts narrows the list."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#malt-list", ListView)
        initial = len(lv.children)

        app.malt_query = "crystal"
        await pilot.pause()

        filtered = len(lv.children)
        assert filtered < initial
        assert filtered > 0


@pytest.mark.asyncio
async def test_hop_filter_narrows_list():
    """Filtering hops narrows the list."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        lv = app.query_one("#hop-list", ListView)
        initial = len(lv.children)

        app.hop_query = "cascade"
        await pilot.pause()

        filtered = len(lv.children)
        assert filtered < initial
        assert filtered > 0


@pytest.mark.asyncio
async def test_select_malt_auto_fills_lovibond():
    """Selecting a malt auto-fills the spec lovibond input."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert len(app._all_malts) > 0

        malt = app._all_malts[0]
        app.malt_query = malt.name
        await pilot.pause()
        lv = app.query_one("#malt-list", ListView)
        lv.focus()
        await pilot.pause()
        lv.action_select_cursor()
        await pilot.pause()

        lovibond_input = app.query_one("#spec-lovibond", Input)
        assert float(lovibond_input.value) == malt.lovibond


@pytest.mark.asyncio
async def test_select_hop_auto_fills_alpha_acid():
    """Selecting a hop auto-fills the alpha acid input."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert len(app._all_hops) > 0

        hop = app._all_hops[0]
        app.hop_query = hop.name
        await pilot.pause()
        lv = app.query_one("#hop-list", ListView)
        lv.focus()
        await pilot.pause()
        lv.action_select_cursor()
        await pilot.pause()

        aa_input = app.query_one("#alpha-acid", Input)
        assert float(aa_input.value) == hop.alpha_acid_pct


@pytest.mark.asyncio
async def test_full_workflow():
    """Full workflow: type values, select style, verify gauges and displays."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 32)) as pilot:
        await pilot.pause()

        # Set recipe values
        app.batch_size_l = 25.0
        app.base_malt_kg = 5.5
        app.spec_malt_kg = 0.4
        app.spec_malt_lovibond = 60.0
        app.hop_weight_g = 40.0
        app.alpha_acid_pct = 8.0
        await pilot.pause()

        og = app.query_one("#og-display", Static)
        ibu = app.query_one("#ibu-display", Static)
        assert "OG:" in _text(og)
        assert "IBU:" in _text(ibu)

        # Select a style
        app.style_query = "IPA"
        await pilot.pause()
        lv = app.query_one("#style-list", ListView)
        assert len(lv.children) > 0
        lv.focus()
        await pilot.pause()
        lv.action_select_cursor()
        await pilot.pause()

        assert app.selected_style is not None
        assert "IPA" in app.selected_style.name or "Double" in app.selected_style.name
        info = app.query_one("#style-info", Static)
        assert app.selected_style.name in _text(info)

        # Verify gauges are visible
        og_g = app.query_one("#og-gauge")
        assert og_g.display

        # Verify inventory button exists
        btn = app.query_one("#btn-inventory")
        assert btn.label == "Build Inventory"

        # Verify theme selector is populated
        ts = app.query_one("#theme-select", Select)
        assert len(ts._options) > 0
