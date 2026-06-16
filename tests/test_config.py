"""Unit tests for brew_tui.config."""

import json
from pathlib import Path

from brew_tui.config import BrewConfig, DEFAULT_RECIPE_DIR


def test_default_values():
    cfg = BrewConfig()
    assert cfg.theme == "textual-dark"
    assert cfg.recipe_path == str(DEFAULT_RECIPE_DIR)


def test_load_missing_file_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    cfg = BrewConfig.load(p)
    assert cfg.theme == "textual-dark"


def test_save_and_load(tmp_path):
    p = tmp_path / "config.json"
    cfg = BrewConfig(theme="gruvbox", recipe_path=str(tmp_path / "recipes"))
    cfg.save(p)

    loaded = BrewConfig.load(p)
    assert loaded.theme == "gruvbox"
    assert loaded.recipe_path == str(tmp_path / "recipes")


def test_save_creates_parent_dir(tmp_path):
    p = tmp_path / "subdir" / "config.json"
    cfg = BrewConfig(theme="catppuccin-mocha", recipe_path=str(tmp_path / "recipes"))
    cfg.save(p)
    assert p.exists()


def test_load_corrupted_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("not json")
    cfg = BrewConfig.load(p)
    assert cfg.theme == "textual-dark"


def test_custom_values_persist(tmp_path):
    p = tmp_path / "config.json"
    cfg = BrewConfig(theme="solarized-light", recipe_path=str(tmp_path / "my"))
    cfg.save(p)

    data = json.loads(p.read_text())
    assert data["theme"] == "solarized-light"
    assert data["recipe_path"] == str(tmp_path / "my")
