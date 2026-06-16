"""Integration / smoke tests for the Textual TUI app."""

import pytest
from textual.widgets import Input, ListView, Select, Static
from brew_tui.app import BrewTUI, MaltAddition, HopAddition


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
    """No malt additions + zero batch uses fallback, no crash."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()

        app._malt_additions.clear()
        app._rebuild_malt_ui()
        app._hop_additions.clear()
        app._rebuild_hop_ui()
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
        fg_g = app.query_one("#fg-gauge")
        abv_g = app.query_one("#abv-gauge")
        assert not og_g.display
        assert not fg_g.display
        assert not abv_g.display

        app.selected_style = app._all_styles[0]
        await pilot.pause()
        assert og_g.display
        assert fg_g.display
        assert abv_g.display

        app.selected_style = None
        await pilot.pause()
        assert not og_g.display
        assert not fg_g.display
        assert not abv_g.display


@pytest.mark.asyncio
async def test_select_style_shows_range_in_display():
    """Selecting a style shows range/status in the display statics."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        og_dis = app.query_one("#og-display", Static)
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
async def test_select_malt_adds_addition():
    """Selecting a malt adds a new MaltAddition row."""
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
        initial_count = len(app._malt_additions)
        lv.action_select_cursor()
        await pilot.pause()

        assert len(app._malt_additions) == initial_count + 1
        added = app._malt_additions[-1]
        assert added.name == malt.name
        assert added.ppg == malt.ppg
        assert added.lovibond == malt.lovibond
        assert added.weight_kg == 1.0  # default


@pytest.mark.asyncio
async def test_select_hop_adds_addition():
    """Selecting a hop adds a new HopAddition row."""
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
        initial_count = len(app._hop_additions)
        lv.action_select_cursor()
        await pilot.pause()

        assert len(app._hop_additions) == initial_count + 1
        added = app._hop_additions[-1]
        assert added.name == hop.name
        assert added.alpha_acid_pct == hop.alpha_acid_pct
        assert added.boil_time_min == 60.0  # default


@pytest.mark.asyncio
async def test_full_workflow():
    """Full workflow: additions, style, verify gauges and displays."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 32)) as pilot:
        await pilot.pause()

        app.batch_size_l = 25.0
        app._malt_additions = [
            MaltAddition("Pale 2-Row", 5.5, 2.0, 37.0),
            MaltAddition("Crystal 60", 0.4, 60.0, 34.0),
        ]
        app._rebuild_malt_ui()
        app._hop_additions = [
            HopAddition("Cascade", 40.0, 8.0, 60.0),
        ]
        app._rebuild_hop_ui()
        app.fg_estimate = 1.012
        await pilot.pause()

        og = app.query_one("#og-display", Static)
        ibu = app.query_one("#ibu-display", Static)
        abv = app.query_one("#abv-display", Static)
        assert "OG:" in _text(og)
        assert "IBU:" in _text(ibu)
        assert "ABV:" in _text(abv)

        app.style_query = "IPA"
        await pilot.pause()
        lv = app.query_one("#style-list", ListView)
        assert len(lv.children) > 0
        lv.focus()
        await pilot.pause()
        lv.action_select_cursor()
        await pilot.pause()

        assert app.selected_style is not None
        assert "IPA" in app.selected_style.name

        info = app.query_one("#style-info", Static)
        assert app.selected_style.name in _text(info)

        assert app.query_one("#og-gauge").display
        assert app.query_one("#fg-gauge").display
        assert app.query_one("#abv-gauge").display

        btn = app.query_one("#btn-inventory")
        assert btn.label == "Build Inventory"

        ts = app.query_one("#theme-select", Select)
        assert len(ts._options) > 0


@pytest.mark.asyncio
async def test_invalid_input_shows_red_border():
    """Non-numeric batch-size input gets .invalid CSS class."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        inp = app.query_one("#batch-size", Input)
        inp.value = "abc"
        await pilot.pause()
        assert "invalid" in inp.classes


@pytest.mark.asyncio
async def test_valid_input_removes_invalid_class():
    """Typing a valid number removes the .invalid CSS class."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        inp = app.query_one("#batch-size", Input)
        inp.value = "abc"
        await pilot.pause()
        assert "invalid" in inp.classes
        inp.value = "25.0"
        await pilot.pause()
        assert "invalid" not in inp.classes


@pytest.mark.asyncio
async def test_batch_size_clamped_low():
    """Batch size is clamped to minimum 0.1."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        inp = app.query_one("#batch-size", Input)
        inp.value = "0.05"
        await pilot.pause()
        assert app.batch_size_l == 0.1


@pytest.mark.asyncio
async def test_fg_estimate_clamped_high():
    """FG estimate is clamped to maximum 1.200."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        inp = app.query_one("#fg-estimate", Input)
        inp.value = "1.300"
        await pilot.pause()
        assert app.fg_estimate == 1.200


@pytest.mark.asyncio
async def test_mash_efficiency_clamped():
    """Mash efficiency is clamped to 1..100 range."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        inp = app.query_one("#mash-efficiency", Input)
        inp.value = "0"
        await pilot.pause()
        assert app.mash_efficiency_pct == 1.0
        inp.value = "150"
        await pilot.pause()
        assert app.mash_efficiency_pct == 100.0


@pytest.mark.asyncio
async def test_is_valid_float():
    """_is_valid_float handles common cases correctly."""
    app = BrewTUI()
    async with app.run_test(headless=True, size=(120, 30)) as pilot:
        await pilot.pause()
        assert app._is_valid_float("1.0")
        assert app._is_valid_float("0")
        assert app._is_valid_float("-5")
        assert app._is_valid_float("1.010")
        assert not app._is_valid_float("")
        assert not app._is_valid_float("abc")
        assert not app._is_valid_float("1.2.3")
        assert not app._is_valid_float(None)
