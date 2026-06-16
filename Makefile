REPO    := https://raw.githubusercontent.com/beerjson/bjcp-json/main/styles
DATA    := src/brew_tui/data
FALLBACK_JSON := $(DATA)/bjcp_styleguide-2021.json

.PHONY: all data test install run clean

all: install data

# ── Data ────────────────────────────────────────────────────────────

$(DATA):
	mkdir -p $(DATA)

data: | $(DATA)
	@echo "Fetching BJCP style guide…"
	curl -fsSL $(REPO)/bjcp_styleguide-2021.json -o $(FALLBACK_JSON).tmp && \
	  mv $(FALLBACK_JSON).tmp $(FALLBACK_JSON) || \
	  { rm -f $(FALLBACK_JSON).tmp; exit 1; }
	@echo "Wrote $(FALLBACK_JSON)"

# ── Package ─────────────────────────────────────────────────────────

install:
	pip install -e .

# ── Tests ───────────────────────────────────────────────────────────

test:
	python -m pytest tests/ -v

# ── Run ─────────────────────────────────────────────────────────────

run:
	python -m brew_tui

# ── Clean ───────────────────────────────────────────────────────────

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; true
