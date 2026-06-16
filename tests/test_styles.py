"""Tests for BJCP style loading, parsing, and searching."""

import json
import pytest
from pathlib import Path
from brew_tui.styles import Style, load_styles, search_styles


# ── Style dataclass & methods ──────────────────────────────────────

class TestStyle:
    def test_create_and_repr(self):
        s = Style(
            name="American IPA",
            category="IPA",
            style_id="21A",
            og_min=1.050, og_max=1.070,
            ibu_min=40, ibu_max=70,
            srm_min=6, srm_max=14,
            abv_min=5.5, abv_max=7.5,
        )
        assert s.name == "American IPA"
        assert s.style_id == "21A"

    def test_og_range_str(self):
        s = _dummy()
        assert s.og_range_str() == "1.050 – 1.070"

    def test_contains_og_within(self):
        assert _dummy().contains_og(1.060) is True

    def test_contains_og_below(self):
        assert _dummy().contains_og(1.040) is False

    def test_contains_og_above(self):
        assert _dummy().contains_og(1.080) is False

    def test_contains_og_on_boundary(self):
        s = _dummy()
        assert s.contains_og(1.050) is True
        assert s.contains_og(1.070) is True

    def test_ibu_status(self):
        s = _dummy()
        assert s.ibu_status(20) == "below"
        assert s.ibu_status(55) == "within"
        assert s.ibu_status(80) == "above"
        assert s.ibu_status(40) == "within"
        assert s.ibu_status(70) == "within"

    def test_srm_status(self):
        s = _dummy()
        assert s.srm_status(2) == "below"
        assert s.srm_status(10) == "within"
        assert s.srm_status(20) == "above"


# ── Full JSON parsing ──────────────────────────────────────────────

class TestLoadStylesFromFile:
    def test_loads_all_styles(self):
        styles = load_styles()
        assert len(styles) >= 90
        assert all(isinstance(s, Style) for s in styles)

    def test_first_style_fields(self):
        styles = load_styles()
        first = styles[0]
        assert first.name == "American Light Lager"
        assert first.style_id == "1A"
        assert first.og_min == pytest.approx(1.028, abs=0.001)
        assert first.og_max == pytest.approx(1.040, abs=0.001)
        assert first.ibu_min == 8
        assert first.ibu_max == 12
        assert first.srm_min == 2
        assert first.srm_max == 3

    def test_ipa_style_present(self):
        styles = load_styles()
        names = [s.name for s in styles]
        assert "American IPA" in names
        assert "Double IPA" in names

    def test_unique_style_ids(self):
        styles = load_styles()
        ids = [s.style_id for s in styles]
        assert len(ids) == len(set(ids))


# ── Fallback loader ────────────────────────────────────────────────

class TestFallbackLoader:
    def test_fallback_not_empty(self):
        styles = load_styles(data_dir="/nonexistent/path")
        assert len(styles) > 0
        assert all(isinstance(s, Style) for s in styles)

    def test_fallback_contains_common_styles(self):
        styles = load_styles(data_dir="/nonexistent/path")
        names = [s.name for s in styles]
        assert "American IPA" in names


# ── Fuzzy search ──────────────────────────────────────────────────

class TestSearchStyles:
    def test_fuzzy_search_ipa(self):
        styles = load_styles()
        results = search_styles(styles, "ipa")
        assert len(results) >= 5
        assert all("ipa" in s.name.lower() for s in results)

    def test_fuzzy_search_stout(self):
        styles = load_styles()
        results = search_styles(styles, "stout")
        assert len(results) >= 3
        assert all("stout" in s.name.lower() for s in results)

    def test_fuzzy_search_empty_query(self):
        styles = load_styles()
        results = search_styles(styles, "")
        assert len(results) == len(styles)

    def test_fuzzy_search_no_match(self):
        styles = load_styles()
        results = search_styles(styles, "xyznonexistent")
        assert len(results) == 0


# ── Helpers ────────────────────────────────────────────────────────

def _dummy() -> Style:
    return Style(
        name="American IPA",
        category="IPA",
        style_id="21A",
        og_min=1.050, og_max=1.070,
        ibu_min=40, ibu_max=70,
        srm_min=6, srm_max=14,
        abv_min=5.5, abv_max=7.5,
    )
