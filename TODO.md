# brew-tui — Build Plan

## ✅ Phase 0: Calculation Engine (Done)
- [x] `_to_float` input guard
- [x] `calculate_og` — PPG-based gravity
- [x] `calculate_srm` / `calculate_srm_from_mcu` — Morey equation
- [x] `calculate_ibu` — simplified Tinseth
- [x] Division-by-zero / empty-input / MCU≤0 guards
- [x] 27 passing pytest tests

## ✅ Phase 1: BJCP Style Data (Done)
- [x] `make data` — curl the BJCP JSON into `src/brew_tui/data/`
- [x] `Style` dataclass with range helpers and status methods
- [x] 16-style embedded fallback for when `make data` hasn't been run
- [x] Loader: local JSON → fallback → skips specialty styles without vital stats
- [x] `search_styles()` with substring + rapidfuzz partial-ratio fallback
- [x] 18 tests (45 total): dataclass, JSON parsing, fallback, fuzzy search

## ✅ Phase 2: TUI Skeleton & Recipe Inputs (Done)
- [x] Two-pane `Horizontal` layout with `Header`/`Footer`
- [x] Left pane: 6 `Input` fields bound to reactive floats via `_to_float`
- [x] Right pane: dashboard placeholder showing OG/SRM/IBU values
- [x] `BrewTUI` app with `_painted` guard to skip init-time widget queries
- [x] Live recalculation on any input change via reactive `watch_*` → `_recalc`
- [x] CSS: dark theme, amber labels, bordered panes
- [x] `__main__.py` entry point + `pyproject.toml` console script
- [x] 5 integration tests (50 total): compose, input update, zero/empty guards

## ✅ Phase 3: Style Dashboard & Gauges (Done)
- [x] `GaugeBar` widget — 20-char horizontal bar with filled track, position marker, and color
- [x] `style-filter` Input + `ListView` with rapidfuzz search (`watch_style_query` → `_populate_style_list`)
- [x] `on_list_view_selected` → sets `selected_style` reactive
- [x] `watch_selected_style` → updates style info, shows gauges with correct min/max, refreshes display statics
- [x] Display static widgets show value + Rich-markup status + style range when style selected
- [x] Gauge colours: **green** (within range), **blue** (below), **red** (above)
- [x] Gauges hidden when no style selected, shown on selection
- [x] Gauges reactively update min/max on style change AND value on recipe change
- [x] 10 app integration tests (55 total): compose, input update, zero/empty, style list, filter, selection, gauges

## ✅ Phase 4: Config & Theme System (Done)
- [x] `BrewConfig` dataclass with `load()` / `save()` — JSON config under `$XDG_CONFIG_HOME/brew-tui/`
- [x] Auto-generates default config file on first run
- [x] Configurable recipe storage path (default: `~/.brew-tui-recipes/`)
- [x] `Ctrl+T` keybinding to cycle through all built-in Textual themes
- [x] Theme `Select` dropdown in the Settings section (right pane)
- [x] Theme change is persisted to config file immediately
- [x] 6 config unit tests (61 total): load, save, corrupted file, custom path, persistence
- [x] 3 theme integration tests (64 total): selector present, theme change, recipe path

## ✅ Phase 5: Ingredient Inventory Browser (Done)
- [x] Bundled 29 common malts (name, PPG, Lovibond) and 26 hops (name, typical AA%)
- [x] `Malt` / `Hop` dataclasses with `search_malts()` / `search_hops()` fuzzy search
- [x] Fuzzy-searchable lists with filter Inputs in the left pane
- [x] Selecting a malt auto-fills the Spec Malt Lovibond field
- [x] Selecting a hop auto-fills the Alpha Acid field
- [x] 9 ingredient unit tests (73 total): dataclass, data loading, substring/fuzzy search
- [x] 6 ingredient integration tests (79 total): lists populated, filters, auto-fill

## ✅ Phase 6: Polish & Packaging (Done)
- [x] Conversational inventory builder (`Ctrl+I` / "Build Inventory" button)
- [x] Friendly interview flow: malts → hops → yeast → specialty grains
- [x] Parsing `name:amount` format for each category
- [x] Inventory persisted to `~/.brew-tui-recipes/inventory.json`
- [x] Inventory items appear in browser lists with `[I]` prefix
- [x] 17 inventory unit tests (97 total): data model, save/load, parsers
- [x] CSS styling — theme-aware `$` variables, focus states, input borders, scrollable left pane
- [x] Snackbar notifications for corrupt inventory, missing style data, theme changes, saved inventory
- [x] `pyproject.toml` entry point — `brew-tui` console script
- [x] Final integration test: set all values, select style, verify gauges and displays

## ✅ Phase 7: Input Limitations & Implied Features (Done)
- [x] Multi-malt additions: dynamic list of (name, weight, lovibond, PPG) rows, add/remove
- [x] Multi-hop additions: dynamic list of (name, weight, AA%, boil_time) rows, add/remove
- [x] Per-hop Tinseth utilization based on boil time
- [x] Mash efficiency % control in UI
- [x] PPG auto-fill from selected malt in addition row
- [x] `calculate_abv()` engine function
- [x] `Style.fg_min` / `Style.fg_max` with range string, status, and contains methods
- [x] ABV gauge on dashboard
- [x] FG gauge on dashboard + FG input field
- [x] Recipe save/load JSON to recipe_path
- [x] New Recipe / Reset button
- [x] Inventory path uses `config.recipe_path` instead of hardcoded path
- [x] Inventory list refreshed on return from inventory builder
- [x] Taller malt/hop/style lists (6 rows), right pane scrollable
- [x] 16 new tests (114 total): ABV, Tinseth util, multi-IBU, Style FG/ABV, dynamic additions

## ✅ Phase 8: UX Polish (Done)
- [x] Screenshots in docs/ and README
- [x] Input validation feedback (red border on parse failure)
- [x] Input value bounds/clamping (batch, FG, efficiency, weights, times)
- [x] Inventory edit/delete screen (view, remove items, delete all)
- [x] Keyboard shortcuts: ctrl+f (style search), ctrl+e (edit inventory)
- [x] Responsive left pane width: 38% with min/max constraints
- [x] Release target: `make release TAG=v0.x.y`
- [x] v0.1-alpha tagged and pushed
- [x] 124 tests total, lint clean, CI passing

## ✅ Phase 9: Multi-Recipe Storage (Done)
- [x] Named recipe save/load with dialog screens
- [x] Open screen lists all saved recipes, select to load
- [x] Sanitized filenames with conflict-free naming
- [x] `_current_recipe_name` tracking for overwrite-on-re-save
- [x] Recipe files stored in `config.recipe_path/{name}.json`
- [x] 6 new tests (130 total), lint clean

## ✅ Phase 10: Imperial Units (Done)
- [x] Unit conversion module (`units.py`) with lb↔kg, oz↔g, gal↔L
- [x] `unit_system` field in config ("imperial" default)
- [x] Batch size label dynamic: "Batch Size (gal)" / "Batch Size (L)"
- [x] Malt weights displayed in lb, hop weights in oz (imperial default)
- [x] Imperial-friendly defaults: 5 gal, 11 lb base malt, 1 oz hop addition
- [x] `ctrl+u` toggles between imperial/metric with live conversion
- [x] Recipe format v2 includes `unit_system` field (values still stored in metric internally)
- [x] 130 tests pass, lint clean

## ✅ Phase 11: Brew Wizard (Done)
- [x] Conversational recipe wizard (`Ctrl+W` / "Brew Wizard" button)
- [x] 9 stages: style, batch size, base malts, specialty malts, hops & schedule, yeast, pitching temp, fermentation time, notes
- [x] Fuzzy matching of style, malt, and hop input against built-in + inventory databases
- [x] Parses `name: weight @ time` format with unit conversion (lb/kg/oz/g)
- [x] Auto-looks up PPG, Lovibond, AA% from ingredient database
- [x] Populates main form on completion — user can still tweak everything
- [x] Recipe format v3 with yeast, pitching temp, fermentation time, notes metadata
- [x] 174 tests pass, lint clean

## ✅ Phase 12: Navigation & Interaction Polish (Done)
- [x] Focus jumps to weight input after selecting malt/hop from list
- [x] Search filter auto-clears after adding an ingredient
- [x] Focus moves to filter input after removing a row (ready to add another)
- [x] Focus batch-size on New Recipe and after loading a recipe
- [x] `Ctrl+N` (New Recipe), `Ctrl+S` (Save As), `Ctrl+O` (Open) shortcuts
- [x] Wider left pane (40→62 cells) for better readability
- [x] Taller ingredient/style lists (6→8 rows)
- [x] 174 tests pass, lint clean

## Up Next
- [ ] **Style checkpoint validation** — after each ingredient stage, check additions against the selected style's range. "Woah there, that's way too bitter for a Kolsch — maybe tone down the bittering hops?"
- [ ] **Quick-paste recipe import** — free-text `TextArea` screen where you paste a recipe in natural format ("10 lbs Pale 2-Row, 1 oz Cascade @ 60...") and it parses into the structured form

## Future
- [ ] Two-column malt/hop rows on wider terminals
- [ ] Tap water / mineral profile inputs
- [ ] Mash temperature steps
- [ ] Hydrometer correction / temperature compensation
- [ ] Export recipe to BeerXML / text / markdown
- [ ] Pull recipes from remote repositories (Brewers Friend API + BeerXML import)
- [ ] Style comparison side-by-side
- [ ] Recipe scaling (batch size only, or full %) 
