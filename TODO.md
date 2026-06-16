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

## 🔲 Phase 4: Ingredient Inventory Browser
- [ ] Bundled common malts (name, PPG, Lovibond) and hops (name, typical AA%)
- [ ] Fuzzy-searchable selection list
- [ ] On select, auto-fill the ingredient fields

## 🔲 Phase 5: Polish & Packaging
- [ ] CSS styling for a clean TUI look
- [ ] Error/snackbar for network failure
- [ ] `pyproject.toml` entry point
- [ ] Final integration test: launch app, type values, verify gauge updates
