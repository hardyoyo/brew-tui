"""Configuration management for brew-tui.

Reads/writes a JSON config file under XDG_CONFIG_HOME.
Auto-generates default config on first run.
"""


import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Self

CONFIG_DIR = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "brew-tui"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_RECIPE_DIR = Path.home() / ".brew-tui-recipes"


@dataclass
class BrewConfig:
    theme: str = "textual-dark"
    recipe_path: str = str(DEFAULT_RECIPE_DIR)

    @classmethod
    def load(cls, path: Path | None = None) -> Self:
        cfg_file = path or CONFIG_FILE
        try:
            if cfg_file.is_file():
                with open(cfg_file) as f:
                    data = json.load(f)
                return cls(
                    theme=data.get("theme", cls.theme),
                    recipe_path=data.get("recipe_path", cls.recipe_path),
                )
        except (json.JSONDecodeError, OSError):
            pass
        return cls()

    def save(self, path: Path | None = None) -> None:
        cfg_file = path or CONFIG_FILE
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg_file, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def ensure_dirs(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.recipe_path).mkdir(parents=True, exist_ok=True)
