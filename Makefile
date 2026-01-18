.PHONY: help install run dev test lint format type-check seed db-upgrade clean infra

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies (Poetry)"
	@echo "  make run           - Run the app (uvicorn)"
	@echo "  make dev           - Run with auto-reload"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run ruff linter"
	@echo "  make format        - Format code with black + ruff"
	@echo "  make type-check    - Run mypy"
	@echo "  make seed          - Seed database with initial data"
	@echo "  make db-upgrade    - Run Alembic migrations"
	@echo "  make infra         - Start dev infrastructure (PostgreSQL via Docker)"
	@echo "  make stop-dev      - Stop dev infrastructure (PostgreSQL via Docker)"
	@echo "  make clean         - Remove cache and temporary files"

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

infra:
	docker-compose --env-file .env.dev -f docker/docker-compose-dev.yml up -d

stop-dev:
	docker-compose --env-file .env.dev -f docker/docker-compose-dev.yml down

clean:
	find . -type d -name '__pycache__' -delete
	find . -type f -name '*.pyc' -delete
	rm -rf .mypy_cache/ .ruff_cache/ .pytest_cache/
