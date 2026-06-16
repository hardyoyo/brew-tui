"""Unit tests for brew_tui.ingredients."""

from brew_tui.ingredients import (
    Malt,
    Hop,
    get_malts,
    get_hops,
    search_malts,
    search_hops,
)


def test_malt_fields():
    m = Malt("Test", 37, 10)
    assert m.name == "Test"
    assert m.ppg == 37
    assert m.lovibond == 10


def test_hop_fields():
    h = Hop("Test", 5.5)
    assert h.name == "Test"
    assert h.alpha_acid_pct == 5.5


def test_get_malts_returns_all():
    malts = get_malts()
    assert len(malts) > 10
    assert all(isinstance(m, Malt) for m in malts)


def test_get_hops_returns_all():
    hops = get_hops()
    assert len(hops) > 10
    assert all(isinstance(h, Hop) for h in hops)


def test_search_malts_empty_query():
    malts = get_malts()
    assert search_malts(malts, "") == malts


def test_search_malts_substring():
    malts = get_malts()
    result = search_malts(malts, "crystal")
    assert len(result) >= 4
    assert all("crystal" in m.name.lower() for m in result)


def test_search_malts_fuzzy():
    malts = get_malts()
    result = search_malts(malts, "choclate")  # misspelled
    assert any("chocolate" in m.name.lower() for m in result)


def test_search_hops_empty_query():
    hops = get_hops()
    assert search_hops(hops, "") == hops


def test_search_hops_substring():
    hops = get_hops()
    result = search_hops(hops, "cascade")
    assert len(result) == 1
    assert result[0].name == "Cascade"


def test_search_hops_fuzzy():
    hops = get_hops()
    result = search_hops(hops, "cascad")  # incomplete
    assert any("cascade" in h.name.lower() for h in result)
