# Usage

## Running brew-tui

```bash
brew-tui
```

Or via Python module:

```bash
python -m brew_tui
```

---

## Recipe Inputs (Left Pane)

The left pane contains six input fields for your recipe:

| Field | Description | Default |
|---|---|---|
| Batch Size (L) | Target batch volume in litres | 20.0 |
| Base Malt (kg) | Base malt weight in kilograms | 5.0 |
| Specialty Malt (kg) | Specialty/steeping malt weight | 0.0 |
| Spec Malt Lovibond | Colour rating of your specialty malt | 10.0 |
| Hop Weight (g) | Hop weight in grams | 30.0 |
| Alpha Acid (%) | Hop alpha-acid percentage | 5.0 |

All fields accept decimal values. Empty or zero inputs are handled gracefully
(the engine uses safe fallbacks rather than crashing).

---

## Style Dashboard (Right Pane)

### Selecting a Style

1. Type in the **Filter styles...** input to fuzzy-search BJCP beer styles.
   - Exact substring matches appear first; if none match, rapidfuzz partial-ratio
     kicks in.
2. Use arrow keys to highlight a style in the list, then press **Enter**.
3. The style info panel shows the style name, code, and target ranges for
   OG, IBU, SRM, and ABV.

### Gauges

When a style is selected, three horizontal gauges appear, one for each metric:

- **Filled track (▓)** shows progress toward the target range.
- **Position marker (●)** shows where your recipe value lands:

  | Colour | Meaning |
  |---|---|
  | Green | Your value is within the style range |
  | Blue | Your value is below the style range |
  | Red | Your value is above the style range |

The display statics above each gauge also show the exact range and a
"below" / "within" / "above" status label.

Deselect the style (press Escape on the list) to hide the gauges.

---

## Ingredient Browser (Left Pane)

Below the input fields are two fuzzy-searchable ingredient lists:

- **Malts** — 29 common malts with Lovibond colour and PPG displayed.
  Selecting a malt auto-fills the **Spec Malt Lovibond** field and moves
  focus to the Specialty Malt weight input.
- **Hops** — 26 common hops with typical alpha-acid percentages.
  Selecting a hop auto-fills the **Alpha Acid (%)** field and moves focus
  to the Hop Weight input.

Search works the same as the style filter: substring match first, then
rapidfuzz fuzzy fallback.

Ingredients you add via the **Build Inventory** wizard appear in these
lists marked with an `[I]` prefix.

---

## Inventory Builder

Press **Ctrl+I** or click the **Build Inventory** button in the Settings
section to open the conversational inventory wizard.

The wizard walks you through four categories:

1. **Malts** — `name:kg` format (e.g. `Pale 2-Row:5, Crystal 60:0.3`)
2. **Hops** — `name:grams` format (e.g. `Cascade:50, Citra:30`)
3. **Yeast** — `name:type` format where type is `ale` or `lager`
4. **Specialty Grains** — same `name:kg` format as malts

Type `skip` at any prompt to move to the next category. The inventory is
saved to `~/.brew-tui-recipes/inventory.json` when you finish.

On next launch, inventory items appear in the ingredient browser lists
with an `[I]` prefix. Selecting them auto-fills the same fields as the
built-in ingredients.

---

## Theme Selection

brew-tui supports all built-in Textual themes.

- Open the **Theme** dropdown in the Settings section (right pane) and
  pick any theme.
- Or press **Ctrl+T** to cycle through available themes.

Your chosen theme is saved to the config file and restored on next launch.

---

## Configuration

Configuration is stored as JSON at:

```
~/.config/brew-tui/config.json
```

A default config is auto-generated on first run. You can edit it manually:

```json
{
  "theme": "textual-dark",
  "recipe_path": "/home/you/.brew-tui-recipes"
}
```

| Key | Default | Description |
|---|---|---|
| `theme` | `"textual-dark"` | Theme name from Textual's built-in themes |
| `recipe_path` | `"~/.brew-tui-recipes"` | Directory for recipe/inventory data |

The inventory file is stored at `<recipe_path>/inventory.json`.

---

## Keybindings

| Key | Action |
|---|---|
| Ctrl+T | Cycle to next theme |
| Ctrl+I | Open inventory builder |
| Tab / Shift+Tab | Move focus between widgets |
| Up / Down | Navigate list items |
| Enter | Select highlighted list item |
| Esc | Close screen / deselect style |

---

## Formulas

| Metric | Formula |
|---|---|
| OG | `SG = 1 + Σ(kg × 2.20462 × PPG × eff) / (L × 0.264172) / 1000` |
| SRM | `MCU = Σ(lb × L) / gal` → `SRM = 1.4922 × MCU^0.6859` |
| IBU | `IBU = g_hop × (AA%/100) × util × 1000 / L` (util = 0.24) |

- Base malt PPG defaults to 37, mash efficiency to 75%.
- SRM uses the Morey equation.
- IBU uses a simplified Tinseth formula with a 60-minute boil utilisation of 24%.
