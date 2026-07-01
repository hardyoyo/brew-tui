"""Tests for brew_tui.inventory data model and parsers."""

from brew_tui.inventory import (
    INVENTORY_FILENAME,
    MaltItem,
    HopItem,
    YeastItem,
    Inventory,
    parse_malts,
    parse_hops,
    parse_yeasts,
    parse_specialty_grains,
)


def test_malt_item_defaults():
    m = MaltItem("Pale")
    assert m.amount_kg == 0.0
    assert m.lovibond == 2.0
    assert m.ppg == 37.0


def test_hop_item_defaults():
    h = HopItem("Cascade", 50)
    assert h.amount_g == 50
    assert h.alpha_acid_pct == 5.0


def test_yeast_item_defaults():
    y = YeastItem("US-05", "ale")
    assert y.packages == 1


def test_inventory_empty():
    inv = Inventory()
    assert not inv.nonempty


def test_inventory_nonempty():
    inv = Inventory(malts=[MaltItem("Pale")])
    assert inv.nonempty


def test_save_and_load(tmp_path):
    p = tmp_path / INVENTORY_FILENAME
    inv = Inventory(
        malts=[MaltItem("Pale", 5.0, 2, 37)],
        hops=[HopItem("Cascade", 50, 5.5)],
        yeasts=[YeastItem("US-05", "ale", 2)],
        specialty_grains=[MaltItem("Flaked Oats", 1.0, 2, 33)],
    )
    inv.save(p)
    assert p.exists()

    loaded = Inventory.load(p)
    assert len(loaded.malts) == 1
    assert loaded.malts[0].name == "Pale"
    assert loaded.malts[0].amount_kg == 5.0
    assert len(loaded.hops) == 1
    assert loaded.hops[0].name == "Cascade"
    assert loaded.hops[0].amount_g == 50
    assert len(loaded.yeasts) == 1
    assert loaded.yeasts[0].name == "US-05"
    assert len(loaded.specialty_grains) == 1


def test_load_missing_file(tmp_path):
    inv = Inventory.load(tmp_path / "nope.json")
    assert not inv.nonempty


def test_load_corrupted(tmp_path):
    p = tmp_path / INVENTORY_FILENAME
    p.write_text("garbage")
    inv = Inventory.load(p)
    assert not inv.nonempty


def test_summary_lines_empty():
    inv = Inventory()
    assert inv.summary_lines() == []


def test_summary_lines_with_items():
    inv = Inventory(
        malts=[MaltItem("Pale", 5.0)],
        hops=[HopItem("Cascade", 50)],
    )
    lines = inv.summary_lines()
    assert "Malts" in lines[0]
    assert "Hops" in lines[1]


# ── Parser tests ──────────────────────────────────────────────────────


def test_parse_malts_basic():
    items = parse_malts("Pale:5, Crystal 60:0.3")
    assert len(items) == 2
    assert items[0].name == "Pale"
    assert items[0].amount_kg == 5.0
    assert items[1].name == "Crystal 60"
    assert items[1].amount_kg == 0.3


def test_parse_malts_empty():
    assert parse_malts("") == []


def test_parse_malts_bare_name():
    items = parse_malts("Pale 2-Row")
    assert len(items) == 1
    assert items[0].name == "Pale 2-Row"
    assert items[0].amount_kg == 0.0


def test_parse_hops_basic():
    items = parse_hops("Cascade:50, Citra:30")
    assert len(items) == 2
    assert items[0].name == "Cascade"
    assert items[0].amount_g == 50


def test_parse_yeasts_basic():
    items = parse_yeasts("US-05:ale, WLP029:lager")
    assert len(items) == 2
    assert items[0].name == "US-05"
    assert items[0].yeast_type == "ale"
    assert items[1].yeast_type == "lager"


def test_parse_yeasts_invalid_type_defaults_ale():
    items = parse_yeasts("Something:hybrid")
    assert items[0].yeast_type == "ale"


def test_parse_specialty_grains():
    items = parse_specialty_grains("Flaked Oats:1, Rice Hulls:0.5")
    assert len(items) == 2
    assert items[0].name == "Flaked Oats"
    assert items[0].amount_kg == 1.0
