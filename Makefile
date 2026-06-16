.PHONY: install install-dev test lint format clean

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
