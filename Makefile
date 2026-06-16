.PHONY: install install-dev test lint format clean screenshots

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check src/ tests/
	black --check --target-version py311 src/ tests/

format:
	black --target-version py311 src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache

screenshots:
	python scripts/screenshots.py
	inkscape docs/images/screenshot-default.svg  \
		--export-filename=docs/images/screenshot-default.png  \
		--export-background=black 2>/dev/null || true
	inkscape docs/images/screenshot-recipe.svg   \
		--export-filename=docs/images/screenshot-recipe.png   \
		--export-background=black 2>/dev/null || true
	inkscape docs/images/screenshot-style.svg    \
		--export-filename=docs/images/screenshot-style.png    \
		--export-background=black 2>/dev/null || true
	inkscape docs/images/screenshot-inventory.svg \
		--export-filename=docs/images/screenshot-inventory.png \
		--export-background=black 2>/dev/null || true
	@echo "Screenshots: docs/images/screenshot-*.png"
