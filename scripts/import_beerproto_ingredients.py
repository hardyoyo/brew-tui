"""Generate beerproto_ingredients.json from the beerproto dataset.

Produces src/brew_tui/data/beerproto_ingredients.json — a bundled lookup
table of malt Lovibond values and hop alpha-acid percentages derived from
the beerproto/BeerJSON standardized dataset.

Usage:
    python scripts/import_beerproto_ingredients.py

Requires the beerproto dataset at ~/.local/share/brew-tui/sources/beerproto-dataset/
(or $BEERPROTO_DIR).
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = (
    Path.home() / ".local/share/brew-tui/sources/beerproto-dataset/json"
)
BEERPROTO_DIR = Path(os.environ.get("BEERPROTO_DIR", DEFAULT_DATASET_DIR))


# ── Hardcoded values for ingredients not in beerproto ──────────────
# (extracts and color-encoded names like "Crystal 20" = 20 °L)

_HARDCODED: dict[str, dict] = {
    # LME
    "Extra Light LME": {"lovibond": 1.5, "ppg": 37},
    "Light LME": {"lovibond": 2.0, "ppg": 36},
    "Amber LME": {"lovibond": 12.0, "ppg": 35},
    "Dark LME": {"lovibond": 20.0, "ppg": 34},
    "Wheat LME": {"lovibond": 3.0, "ppg": 36},
    "Pilsner LME": {"lovibond": 1.5, "ppg": 37},
    "Munich LME": {"lovibond": 9.0, "ppg": 35},
    "Rye LME": {"lovibond": 4.0, "ppg": 35},
    # DME
    "Extra Light DME": {"lovibond": 2.0, "ppg": 44},
    "Light DME": {"lovibond": 3.0, "ppg": 44},
    "Amber DME": {"lovibond": 12.0, "ppg": 43},
    "Dark DME": {"lovibond": 22.0, "ppg": 42},
    "Wheat DME": {"lovibond": 3.0, "ppg": 44},
    "Pilsner DME": {"lovibond": 2.0, "ppg": 44},
    "Munich DME": {"lovibond": 9.0, "ppg": 43},
    "Rye DME": {"lovibond": 4.0, "ppg": 43},
    "Rice DME": {"lovibond": 1.0, "ppg": 44},
    # Crystal — color encoded in name
    "Crystal 20": {"lovibond": 20, "ppg": 34},
    "Crystal 40": {"lovibond": 40, "ppg": 34},
    "Crystal 60": {"lovibond": 60, "ppg": 34},
    "Crystal 80": {"lovibond": 80, "ppg": 34},
    "CaraMunich I": {"lovibond": 35, "ppg": 33},
    "CaraMunich II": {"lovibond": 45, "ppg": 33},
    "CaraMunich III": {"lovibond": 60, "ppg": 33},
    # Dark malts — these vary widely across maltsters (~250-750 °L).
    # Use well-known homebrew reference values that match Brewfather.
    "Chocolate": {"lovibond": 259, "ppg": 30},
    "Roasted Barley": {"lovibond": 300, "ppg": 30},
    "Black Patent": {"lovibond": 370, "ppg": 30},
}


# ── Curated name → beerproto name-pattern matching ──────────────────
# For each curated ingredient, a list of specific beerproto entry names
# (case-insensitive substring match) to include and colours to assign.
# If the list is empty, the ingredient's Lovibond is computed by averaging
# EBC values from entries matching the include keywords.
#
# Structure: (include_keywords, exclude_keywords, explicit_entries | None)
#   include_keywords:  at least one must be a substring of the beerproto name
#   exclude_keywords:  if any match, the entry is skipped
#   explicit_entries:  list of exact beerproto entry names to use (if None,
#                       all matching entries are included)

_MALT_MAP: dict[str, tuple[list[str], list[str], list[str] | None]] = {
    # ── Base malts ────────────────────────────────────────────
    "Pale 2-Row": (
        ["pale", "2-row"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "munich",
            "vienna",
            "smoked",
            "aromatic",
            "biscuit",
            "victory",
            "honey",
            "acid",
            "special",
            "dextrin",
            "pils",
            "wheat",
            "rye",
            "oats",
            "torrefi",
            "flaked",
            "naked",
        ],
        ["Pale Ale Malt"],
    ),
    "Pale 6-Row": (
        ["6-row"],
        ["roast", "chocolate", "black"],
        ["Rahr Standard 6-Row"],
    ),
    "Pilsner": (
        ["pilsner", "pilsen"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "munich",
            "smoked",
            "acid",
            "honey",
            "wheat",
            "vienna",
            "rye",
            "special",
            "oats",
            "torrefi",
            "flaked",
            "red",
        ],
        None,
    ),
    "Vienna": (
        ["vienna"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "smoked",
            "acid",
            "honey",
            "wheat",
            "special",
            "terroir",
            "pils",
            "rye",
            "flaked",
        ],
        None,
    ),
    "Munich": (
        ["munich"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "smoked",
            "acid",
            "honey",
            "wheat",
            "special",
            "vienna",
            "aromatic",
            "pils",
            "rye",
            "flaked",
            "caramunich",
            "caramel",
            "dark",
            "goldswaen",
        ],
        None,
    ),
    "Maris Otter": (
        ["maris otter"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "wheat",
            "torrefi",
            "flaked",
        ],
        None,
    ),
    # ── Wheat, oats, adjuncts ────────────────────────────────
    "Wheat Malt": (
        ["wheat"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "smoked",
            "acid",
            "torrefi",
            "flaked",
            "raw",
            "red",
            "pale",
            "pils",
            "munich",
            "vienna",
            "white",
            "dark",
            "caramunich",
            "spelt",
            "naked",
            "oats",
            "rye",
            "unmalted",
            "midnight",
            "cafe",
            "chocolat",
            "eclipse",
            "melanoidin",
            "cara wheat",
            "buckwheat",
            "toasted",
            "goldswaen",
            "arome",
            "blond",
            "ruby",
        ],
        None,
    ),
    "Flaked Wheat": (
        ["flaked wheat", "torrefied wheat"],
        ["chocolate", "black", "roast", "crystal", "caramel"],
        None,
    ),
    "Flaked Oats": (
        ["flaked oat", "rolled oat", "oat"],
        [
            "roast",
            "chocolate",
            "black",
            "caramel",
            "crystal",
            "smoked",
            "naked",
            "stout",
            "wheat",
            "rye",
            "barley",
        ],
        None,
    ),
    # ── Specialty malts ──────────────────────────────────────
    "Cara-Pils": (
        ["cara-pils", "carapils", "dextrine"],
        ["copper", "roast", "chocolate"],
        ["Carapils\u00ae Malt", "Weyermann\u00ae CARAPILS\u00ae"],
    ),
    "CaraAroma": (
        ["cara aroma", "caraaroma"],
        ["special", "roasted", "chocolate"],
        None,
    ),
    "Special B": (
        ["special b"],
        [],
        None,
    ),
    "Biscuit": (
        ["biscuit"],
        [
            "honey",
            "chocolate",
            "black",
            "roasted",
            "caramel",
            "special",
            "wheat",
            "rye",
            "goldswaen",
        ],
        None,
    ),
    "Victory": (
        ["victory"],
        [],
        ["Victory\u00ae Malt"],
    ),
    "Aromatic": (
        ["aromatic"],
        ["black", "chocolate", "roasted", "caramel", "special", "munich"],
        ["Aromatic Malt"],
    ),
    "Melanoidin": (
        ["melanoidin"],
        [],
        None,
    ),
    "Honey": (
        ["honey"],
        ["chocolate", "black", "roasted", "special", "biscuit"],
        None,
    ),
    "Chocolate": (
        ["chocolate"],
        [
            "pale",
            "wheat",
            "rye",
            "naked",
            "roasted barley",
            "flaked",
            "spelt",
            "light",
            "midnight",
            "eclipse",
        ],
        # Use well-known maltster references instead of averaging all
        # (the dataset ranges 254-736 °L which skews the generic average)
        ["Chocolate Malt"],  # matches Barrett Burston (500 EBC) and Briess (690 EBC)
    ),
    "Roasted Barley": (
        ["roasted barley"],
        ["chocolate", "flaked", "unmalted", "pealed"],
        ["Roasted Barley"],  # matches Barrett Burston (1000 EBC) and Briess (591 EBC)
    ),
    "Black Patent": (
        ["black patent", "black malt"],
        ["chocolate", "roasted barley", "pale", "wheat", "caramel", "pearled", "flour"],
        ["Black Malt"],  # matches Briess (985 EBC), Crisp (1540), etc.
    ),
    "Acidulated": (
        ["acidulated", "acid malt", "sauermalz"],
        [],
        None,
    ),
    "Smoked": (
        ["smoked", "rauchmalz"],
        ["chocolate", "black", "caramel", "acid", "wheat", "pils", "vienna", "munich"],
        None,
    ),
}


# ── Hop name matching ──────────────────────────────────────────────

_HOP_MAP: dict[str, list[str]] = {
    "Cascade": ["cascade"],
    "Centennial": ["centennial"],
    "Chinook": ["chinook"],
    "Citra": ["citra"],
    "Mosaic": ["mosaic"],
    "Simcoe": ["simcoe"],
    "Amarillo": ["amarillo"],
    "Columbus": ["columbus", "tomahawk", "zeus", "ctz"],
    "Magnum": ["magnum"],
    "Saaz": ["saaz", "žatecký"],
    "Hallertau Mittelfrüh": [
        "hallertau mittelfrüh",
        "hallertau mf",
        "hallertauer mittelfrüh",
    ],
    "Tettnang": ["tettnang", "tettnanger"],
    "East Kent Golding": ["east kent golding", "ekg"],
    "Fuggle": ["fuggle"],
    "Willamette": ["willamette"],
    "Northern Brewer": ["northern brewer"],
    "Perle": ["perle"],
    "Target": ["target"],
    "Styrian Golding": ["styrian golding", "styrian"],
    "Motueka": ["motueka"],
    "Nelson Sauvin": ["nelson sauvin"],
    "Galaxy": ["galaxy"],
    "Sorachi Ace": ["sorachi ace"],
    "Glacier": ["glacier"],
    "Mt. Hood": ["mt. hood", "mount hood"],
    "Sterling": ["sterling"],
}

_HARDCODED_HOPS: dict[str, float] = {
    "Cascade": 5.5,
    "Centennial": 10.0,
    "Chinook": 12.0,
    "Citra": 13.0,
    "Mosaic": 12.0,
    "Simcoe": 13.0,
    "Amarillo": 9.0,
    "Columbus": 14.0,
    "Magnum": 13.0,
    "Saaz": 3.5,
    "Hallertau Mittelfrüh": 4.0,
    "Tettnang": 4.5,
    "East Kent Golding": 5.0,
    "Fuggle": 4.5,
    "Willamette": 5.0,
    "Northern Brewer": 8.0,
    "Perle": 8.0,
    "Target": 11.0,
    "Styrian Golding": 5.0,
    "Motueka": 7.0,
    "Nelson Sauvin": 12.0,
    "Galaxy": 14.0,
    "Sorachi Ace": 12.0,
    "Glacier": 6.0,
    "Mt. Hood": 5.5,
    "Sterling": 7.0,
}

_HARDCODED_PPG: dict[str, int] = {
    "Pale 2-Row": 37,
    "Pale 6-Row": 35,
    "Pilsner": 37,
    "Vienna": 36,
    "Munich": 35,
    "Maris Otter": 38,
    "Wheat Malt": 38,
    "Flaked Wheat": 37,
    "Flaked Oats": 33,
    "Cara-Pils": 33,
    "CaraAroma": 33,
    "Special B": 30,
    "Biscuit": 34,
    "Victory": 34,
    "Aromatic": 35,
    "Melanoidin": 35,
    "Honey": 34,
    "Chocolate": 30,
    "Roasted Barley": 30,
    "Black Patent": 30,
    "Acidulated": 35,
    "Smoked": 37,
}


# ── Helpers ────────────────────────────────────────────────────────


def _matches(name: str, include: list[str], exclude: list[str]) -> bool:
    nl = name.lower()
    if not any(kw.lower() in nl for kw in include):
        return False
    if any(kw.lower() in nl for kw in exclude):
        return False
    return True


# ── Compute malt values ────────────────────────────────────────────


def compute_malt_values(ferms: list[dict]) -> dict[str, dict]:
    all_names: set[str] = set(_MALT_MAP) | set(_HARDCODED)
    result: dict[str, dict] = {}

    for name in sorted(all_names):
        if name in _HARDCODED:
            hc = _HARDCODED[name]
            result[name] = {
                "lovibond": hc["lovibond"],
                "ppg": hc["ppg"],
                "ebc": round(hc["lovibond"] * 1.97, 1),
                "n": 0,
                "source": "hardcoded",
            }
            continue

        inc, exc, explicit = _MALT_MAP[name]

        if explicit:
            matches = [f for f in ferms if f["name"] in explicit]
        else:
            matches = [f for f in ferms if _matches(f["name"], inc, exc)]

        ebc_vals = []
        for m in matches:
            c = m.get("color")
            if c and c.get("value") is not None and c.get("unit") == "EBC":
                ebc_vals.append(c["value"])

        ppg = _HARDCODED_PPG.get(name, 35)

        if ebc_vals:
            avg_ebc = sum(ebc_vals) / len(ebc_vals)
            result[name] = {
                "lovibond": round(avg_ebc / 1.97, 1),
                "ppg": ppg,
                "ebc": round(avg_ebc, 1),
                "n": len(ebc_vals),
                "source": "beerproto",
            }
        else:
            result[name] = {
                "lovibond": ppg,  # fallback — use PPG as placeholder
                "ppg": ppg,
                "ebc": None,
                "n": 0,
                "source": "fallback",
            }

    return result


# ── Compute hop values ─────────────────────────────────────────────


def compute_hop_values(hops_data: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for name, keywords in _HOP_MAP.items():
        matches = [
            h
            for h in hops_data
            if any(kw.lower() in h["name"].lower() for kw in keywords)
        ]

        aa_vals = []
        for h in matches:
            aa = h.get("alphaAcid", {})
            if aa.get("value") is not None and aa.get("unit") == "PERCENT_SIGN":
                aa_vals.append(aa["value"])

        if aa_vals:
            avg_aa = sum(aa_vals) / len(aa_vals)
            origins = sorted({h["origin"] for h in matches if h.get("origin")})
            result[name] = {
                "alpha_acid_pct": round(avg_aa, 1),
                "n": len(aa_vals),
                "origins": origins[:4],
                "source": "beerproto",
            }
        else:
            fallback = _HARDCODED_HOPS.get(name)
            result[name] = {
                "alpha_acid_pct": fallback,
                "n": 0,
                "origins": [],
                "source": "hardcoded" if fallback else "none",
            }

    return result


# ── Main ───────────────────────────────────────────────────────────


def main():
    if not BEERPROTO_DIR.exists():
        print(f"beerproto dataset not found at {BEERPROTO_DIR}", file=sys.stderr)
        print(
            "Clone:  git clone https://github.com/beerproto/dataset.git",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading dataset from {BEERPROTO_DIR} …")

    with open(BEERPROTO_DIR / "fermentable.json") as f:
        ferms = json.load(f)["fermentables"]
    with open(BEERPROTO_DIR / "hops.json") as f:
        hops_data = json.load(f)["hopVarieties"]

    malts = compute_malt_values(ferms)
    hop_vals = compute_hop_values(hops_data)

    # Print summary
    print("\n── Malts ──────────────────────────────────────")
    for name in sorted(malts):
        m = malts[name]
        lov = m["lovibond"]
        ebc = m["ebc"]
        print(
            f"  {name:20s}  {lov:>6.1f} °L  ppg={m['ppg']}  ({ebc if ebc else '?':>5})  {m['source']}"
        )

    print("\n── Hops ───────────────────────────────────────")
    for name in sorted(hop_vals):
        h = hop_vals[name]
        aa = h["alpha_acid_pct"]
        if aa:
            print(f"  {name:25s}  {aa:5.1f}% AA  (n={h['n']}, {h['source']})")
        else:
            print(f"  {name:25s}  — no data ({h['source']})")

    # Write output JSON
    output = {
        "format_version": 1,
        "source": "beerproto/dataset",
        "source_url": "https://github.com/beerproto/dataset",
        "ebc_to_lovibond_factor": 1.97,
        "malts": malts,
        "hops": hop_vals,
    }

    out_path = REPO_ROOT / "src" / "brew_tui" / "data" / "beerproto_ingredients.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
