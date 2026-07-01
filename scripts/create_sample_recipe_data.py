"""Import sample recipes from online archives into brew-tui format.

Usage:
    python scripts/create_sample_recipe_data.py

Supported sources:
    1. mattsah/beer-recipes  — Markdown homebrew recipes from GitHub
"""

import json
import os
import re
import sys
from pathlib import Path

SOURCES_DIR = (
    Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    / "brew-tui"
    / "sources"
)
BEER_RECIPES_DIR = SOURCES_DIR / "mattsah-beer-recipes"
BEERPROTO_DIR = SOURCES_DIR / "beerproto-dataset"
BEER_RECIPES_REPO = "https://github.com/mattsah/beer-recipes.git"
BEERPROTO_REPO = "https://github.com/beerproto/dataset.git"

RECIPE_OUTPUT_DIR = Path(
    os.environ.get("BREW_TUI_RECIPE_DIR", "~/.brew-tui-recipes")
).expanduser()

GIT_BIN = "git"


def _sanitize(name: str) -> str:
    name = name.strip()
    if not name:
        return "unnamed"
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)


def _clone_repo(url: str, dest: Path) -> None:
    if dest.is_dir():
        print(f"  {dest} exists, skipping clone.")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Cloning {url} ...")
    ret = os.system(f"{GIT_BIN} clone --depth 1 --single-branch {url} {dest}")
    if ret != 0:
        print(f"  Error: clone failed (returned {ret})")
        sys.exit(1)


def _find_recipe_files(repo_dir: Path) -> list[Path]:
    md_files = sorted(repo_dir.rglob("*.md"))
    return [f for f in md_files if f.name not in ("README.md", "Brewing Basics.md")]


def _load_beerproto_fermentables() -> dict:
    path = BEERPROTO_DIR / "json" / "fermentable.json"
    if not path.is_file():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    index: dict[str, dict] = {}
    for item in data.get("fermentables", []):
        name = item.get("name", "").lower().strip()
        if not name:
            continue
        color_value = None
        color_unit = None
        if (
            "color" in item
            and "value" in item["color"]
            and item["color"]["value"] is not None
        ):
            color_value = item["color"]["value"]
            color_unit = item["color"].get("unit", "EBC")
        potential = None
        if (
            "yield" in item
            and "potential" in item["yield"]
            and "value" in item["yield"]["potential"]
        ):
            potential = item["yield"]["potential"]["value"]
        index[name] = {"color": (color_value, color_unit), "ppg": potential}
    return index


def _load_beerproto_hops() -> dict:
    path = BEERPROTO_DIR / "json" / "hops.json"
    if not path.is_file():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    index: dict[str, float | None] = {}
    for item in data.get("hopVarieties", []):
        name = item.get("name", "").lower().strip()
        if not name:
            continue
        alpha = None
        if (
            "alphaAcids" in item
            and "typicalValues" in item["alphaAcids"]
            and "value" in item["alphaAcids"]["typicalValues"]
        ):
            alpha = float(item["alphaAcids"]["typicalValues"]["value"])
        index[name] = alpha
    return index


def _lovibond_from_ebc(ebc: float) -> float:
    return ebc / 1.97


def _lookup_malt(name: str, fermentables: dict) -> dict:
    key = name.lower().strip()
    if key in fermentables:
        info = fermentables[key]
        color = 2.0
        ppg = 37.0
        if info["color"][0] is not None:
            val, unit = info["color"]
            if unit == "EBC":
                color = round(_lovibond_from_ebc(val), 1)
            else:
                color = val
        if info["ppg"] is not None:
            ppg = float(info["ppg"])
        return {"lovibond": color, "ppg": ppg}
    return {"lovibond": 2.0, "ppg": 37.0}


def _lookup_hop(name: str, hops_index: dict) -> float:
    key = name.lower().strip()
    alpha = hops_index.get(key)
    if alpha is not None:
        return float(alpha)
    return 5.0


KNOWN_HOP_NAMES = {
    "cascade",
    "citra",
    "amarillo",
    "centennial",
    "chinook",
    "simcoe",
    "mosaic",
    "hallertau",
    "saaz",
    "tettnang",
    "fuggle",
    "willamette",
    "liberty",
    "brewers gold",
    "us fuggle",
    "us brewers gold",
    "northern brewer",
    "kent golding",
    "east kent golding",
    "columbus",
    "tomahawk",
    "zeus",
    "ctz",
    "warrior",
    "magnum",
    "galaxy",
    "nelsonsauvin",
    "motueka",
    "raku",
    "wakatu",
    "sorachi ace",
    "sterling",
    "styrian golding",
    "goldings",
    "perle",
    "hersbrucker",
    "spalt",
    "strissespalt",
    "mt hood",
    "crystal",
    "vanguard",
    "horizon",
    "millennium",
    "newport",
    "apollo",
    "bravo",
    "summit",
    "super galena",
    "challenger",
    "target",
    "northdown",
    "yeoman",
    "bramling cross",
    "progress",
    "pioneer",
    "admiral",
    "first gold",
    "erald",
    "fuggles",
    "cluster",
    "galena",
    "nugget",
    "willamette",
    "tahoma",
}


def _parse_recipe(path: Path, fermentables: dict, hops_index: dict) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    og = None
    fg = None
    batch_size_gal = None
    malts: list[dict] = []
    hops: list[dict] = []
    in_ingredients = False
    ingredient_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if re.match(r"^##\s+Ingredients", line, re.IGNORECASE):
            in_ingredients = True
            i += 1
            continue

        if in_ingredients:
            if re.match(r"^##\s+\w", line):
                in_ingredients = False
                i += 1
                continue
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                ingredient_lines.append(stripped[2:])
            elif stripped:
                ingredient_lines.append(stripped)

        m_og = re.search(r"OG:?\s*([\d.]+)", line, re.IGNORECASE)
        if m_og:
            og = float(m_og.group(1))
        m_fg = re.search(r"FG:?\s*([\d.]+)", line, re.IGNORECASE)
        if m_fg:
            fg = float(m_fg.group(1))

        i += 1

    last_hop_name: str | None = None
    schedule_lines: list[str] = []

    for ing in ingredient_lines:
        m_batch = re.match(r"([\d.]+)\s*Gallons?\s+of?\s*Water", ing, re.IGNORECASE)
        if m_batch:
            batch_size_gal = float(m_batch.group(1))
            continue
        m_batch2 = re.match(r"([\d.]+)\s*Gallons?\s+Water", ing, re.IGNORECASE)
        if m_batch2:
            batch_size_gal = float(m_batch2.group(1))
            continue

        m_sched_oz = re.match(
            r"([\d.]+)\s*oz\s+([^@]*?)\s*@\s*([\d.]+)", ing, re.IGNORECASE
        )
        if m_sched_oz:
            qty = float(m_sched_oz.group(1))
            name = m_sched_oz.group(2).strip()
            time_min = float(m_sched_oz.group(3))
            if name:
                alpha = _lookup_hop(name, hops_index)
                hops.append(
                    {
                        "name": name,
                        "weight_oz": qty,
                        "alpha_acid_pct": alpha,
                        "boil_time_min": time_min,
                    }
                )
                last_hop_name = name
            elif last_hop_name:
                alpha = _lookup_hop(last_hop_name, hops_index)
                hops.append(
                    {
                        "name": last_hop_name,
                        "weight_oz": qty,
                        "alpha_acid_pct": alpha,
                        "boil_time_min": time_min,
                    }
                )
            else:
                schedule_lines.append(ing)
            continue

        m_sched_naked = re.match(r"([\d.]+)\s*@\s*([\d.]+)", ing)
        if m_sched_naked:
            schedule_lines.append(ing)
            continue

        m_grain_lb = re.match(r"([\d.]+)\s*#\s+(.+?)(?:\s*\([^)]*\))?\s*$", ing)
        if m_grain_lb:
            qty_lb = float(m_grain_lb.group(1))
            name = m_grain_lb.group(2).strip()
            info = _lookup_malt(name, fermentables)
            malts.append(
                {
                    "name": name,
                    "weight_lb": qty_lb,
                    "lovibond": info["lovibond"],
                    "ppg": info["ppg"],
                }
            )
            continue

        m_grain_lb2 = re.match(
            r"([\d.]+)\s*lbs?\s+(.+?)(?:\s*\([^)]*\))?\s*$", ing, re.IGNORECASE
        )
        if m_grain_lb2:
            qty_lb = float(m_grain_lb2.group(1))
            name = m_grain_lb2.group(2).strip()
            info = _lookup_malt(name, fermentables)
            malts.append(
                {
                    "name": name,
                    "weight_lb": qty_lb,
                    "lovibond": info["lovibond"],
                    "ppg": info["ppg"],
                }
            )
            continue

        m_oz = re.match(
            r"([\d.]+)\s*oz\s+(.+?)(?:\s*\([^)]*\))?\s*$", ing, re.IGNORECASE
        )
        if m_oz:
            qty_oz = float(m_oz.group(1))
            name = m_oz.group(2).strip()
            lower_name = name.lower()
            is_hop = (
                lower_name in KNOWN_HOP_NAMES
                or lower_name.rstrip("s") in KNOWN_HOP_NAMES
            )
            if is_hop:
                alpha = _lookup_hop(name, hops_index)
                hops.append(
                    {
                        "name": name,
                        "weight_oz": qty_oz,
                        "alpha_acid_pct": alpha,
                        "boil_time_min": 60.0,
                    }
                )
                last_hop_name = name
            else:
                info = _lookup_malt(name, fermentables)
                malts.append(
                    {
                        "name": name,
                        "weight_lb": qty_oz / 16.0,
                        "lovibond": info["lovibond"],
                        "ppg": info["ppg"],
                    }
                )
            continue

    for hop in hops:
        if hop["alpha_acid_pct"] is None:
            hop["alpha_acid_pct"] = _lookup_hop(hop["name"], hops_index)

    if batch_size_gal is None:
        batch_size_gal = 5.0

    recipe_dict = {
        "version": 3,
        "unit_system": "imperial",
        "batch_size_l": round(batch_size_gal * 3.78541, 1),
        "fg_estimate": fg or 1.010,
        "mash_efficiency_pct": 72.0,
        "malt_additions": [
            {
                "name": m["name"],
                "weight_kg": round(m["weight_lb"] * 0.453592, 3),
                "lovibond": m["lovibond"],
                "ppg": m["ppg"],
            }
            for m in malts
        ],
        "hop_additions": [
            {
                "name": h["name"],
                "weight_g": round(h["weight_oz"] * 28.3495, 1),
                "alpha_acid_pct": h["alpha_acid_pct"],
                "boil_time_min": h["boil_time_min"],
            }
            for h in hops
        ],
    }

    if og is not None:
        recipe_dict["og_estimate"] = og

    return recipe_dict


def _pick_recipes_interactive(recipes: list[Path]) -> list[Path]:
    print(f"\nFound {len(recipes)} recipes:\n")
    for idx, path in enumerate(recipes, start=1):
        title = path.stem
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            m = re.match(r"^#\s+(.+)", line)
            if m:
                title = m.group(1).strip()
                break
        rel = path.relative_to(BEER_RECIPES_DIR)
        print(f"  {idx:3d}. {title}  ({rel})")

    print()
    while True:
        raw = input("Enter recipe numbers to import (comma-separated): ").strip()
        if not raw:
            print("No selection. Exiting.")
            return []
        try:
            indices = [int(x.strip()) for x in raw.split(",")]
        except ValueError:
            print("Invalid input. Enter numbers like: 1,2,3")
            continue
        out: list[Path] = []
        for idx in indices:
            if 1 <= idx <= len(recipes):
                out.append(recipes[idx - 1])
            else:
                print(f"  Skipping invalid number: {idx}")
        if not out:
            print("No valid selections.")
            continue
        return out


def _import_recipe(recipe_file: Path, fermentables: dict, hops_index: dict) -> None:
    recipe_dict = _parse_recipe(recipe_file, fermentables, hops_index)
    if recipe_dict is None:
        print(f"  Skipping {recipe_file.name} (parse failed)")
        return

    title = "Unknown"
    for line in recipe_file.read_text(encoding="utf-8", errors="replace").split("\n"):
        m = re.match(r"^#\s+(.+)", line)
        if m:
            title = m.group(1).strip()
            break
    else:
        title = recipe_file.stem

    recipe_dict["name"] = title
    try:
        rel = recipe_file.relative_to(BEER_RECIPES_DIR)
        if len(rel.parts) > 1:
            recipe_dict["style_name"] = rel.parts[0]
    except ValueError:
        pass

    output_name = _sanitize(title)
    output_path = RECIPE_OUTPUT_DIR / f"{output_name}.json"
    RECIPE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(recipe_dict, f, indent=2)

    malt_count = len(recipe_dict["malt_additions"])
    hop_count = len(recipe_dict["hop_additions"])
    batch_gal = round(recipe_dict["batch_size_l"] / 3.78541, 1)
    print(
        f"  → {output_name}.json  ({malt_count} malts, {hop_count} hops, "
        f"{batch_gal} gal batch)"
    )


def main() -> None:
    print("brew-tui Sample Recipe Importer\n")

    print("[1/4] Cloning mattsah/beer-recipes ...")
    _clone_repo(BEER_RECIPES_REPO, BEER_RECIPES_DIR)

    print("[2/4] Loading beerproto ingredient data ...")
    _clone_repo(BEERPROTO_REPO, BEERPROTO_DIR)
    fermentables = _load_beerproto_fermentables()
    hops_index = _load_beerproto_hops()
    f_count = len(fermentables)
    h_count = len(hops_index)
    print(f"  Loaded {f_count} fermentables, {h_count} hop varieties")

    print("[3/4] Scanning recipes ...")
    recipes = _find_recipe_files(BEER_RECIPES_DIR)
    if not recipes:
        print("  No recipe files found!")
        sys.exit(1)

    selected = _pick_recipes_interactive(recipes)
    if not selected:
        print("Done.")
        return

    print(f"\n[4/4] Importing {len(selected)} recipe(s) ...")
    for recipe_file in selected:
        print(f"  {recipe_file.name}")
        _import_recipe(recipe_file, fermentables, hops_index)

    print(f"\nDone! Recipes saved to {RECIPE_OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
