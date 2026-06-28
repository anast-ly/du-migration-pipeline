.PHONY: install lint test run up down clean

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests

test:
	pytest tests/ -v --cov=src/migration

run:
	python -m src.migration

up:
	docker-compose up --build

down:
	docker-compose down -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
