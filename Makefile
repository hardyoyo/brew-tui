.PHONY: help install install-dev test lint format clean \
        create-sample-recipe-data screenshots release coverage

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

install-dev: ## Install with dev dependencies
	pip install -e ".[dev]"

test: ## Run all tests
	pytest -v

coverage: ## Run tests with coverage report
	pytest --cov --cov-report=term-missing

lint: ## Lint source and tests (ruff + black --check)
	ruff check src/ tests/
	black --check --target-version py311 src/ tests/

format: ## Auto-format source and tests with black
	black --target-version py311 src/ tests/

clean: ## Remove cache and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache

create-sample-recipe-data: ## Import sample recipes from mattsah/beer-recipes
	python scripts/create_sample_recipe_data.py

screenshots: ## Generate SVG screenshots for documentation
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

release: ## Tag and push a release (use TAG=v0.x.y)
	@if [ -z "$(TAG)" ]; then echo "Usage: make release TAG=v0.x.y"; exit 1; fi
	@if [ "$(shell git rev-parse --abbrev-ref HEAD)" != "main" ]; then \
		echo "Must be on main branch"; exit 1; fi
	@if [ -n "$(shell git status --porcelain)" ]; then \
		echo "Uncommitted changes"; exit 1; fi
	make lint
	make test
	git tag -a "$(TAG)" -m "Release $(TAG)"
	git push origin "$(TAG)"
	@echo "Tagged and pushed $(TAG)"
