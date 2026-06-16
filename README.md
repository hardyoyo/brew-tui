# brew-tui

An interactive homebrew recipe helper that runs in your terminal.

Built with [Textual](https://textual.textualize.io/). Type in ingredients and see live OG, SRM, and IBU gauges against BJCP style guidelines.

## Quick Start

```bash
pip install -e .
python -m brew_tui
```

## Features

- **Live calculation engine** — Original Gravity (OG), SRM color, and IBU bitterness update as you type
- **BJCP style dashboard** — fuzzy-search through official style guidelines; see your recipe's position relative to style brackets
- **Visual gauges** — colour-coded progress bars show below/in/above range at a glance
- **Ingredient inventory** — fuzzy-searchable lists of common malts and hops
- **Crash-safe** — empty or zero inputs are handled gracefully (no division-by-zero)

## Formulas

| Metric | Formula |
|---|---|
| OG | `SG = 1 + Σ(kg × 2.20462 × PPG × eff) / (L × 0.264172) / 1000` |
| SRM | `MCU = Σ(lb × L) / gal` → `SRM = 1.4922 × MCU^0.6859` |
| IBU | `IBU = g_hop × (AA%/100) × util × 1000 / L` (util = 0.24) |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

BSD 0-Clause
