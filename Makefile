.PHONY: help install run dev test lint format type-check seed db-upgrade clean

help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies (Poetry)"
	@echo "  run           - Run the app (uvicorn)"
	@echo "  dev           - Run with auto-reload"
	@echo "  test          - Run tests"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Format code with black + ruff"
	@echo "  type-check    - Run mypy"
	@echo "  seed          - Seed database with initial data"
	@echo "  db-upgrade    - Run Alembic migrations"
	@echo "  clean         - Remove cache and temporary files"

install:
	poetry install

run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	poetry run pytest

lint:
	poetry run ruff check .

format:
	poetry run black .
	poetry run ruff check . --fix

type-check:
	poetry run mypy app/

seed:
	poetry run python -m app.db.seed

db-upgrade:
	poetry run alembic upgrade head

clean:
	find . -type d -name '__pycache__' -delete
	find . -type f -name '*.pyc' -delete
	rm -rf .mypy_cache/ .ruff_cache/ .pytest_cache/