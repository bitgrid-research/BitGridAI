.PHONY: check fmt lint test test-unit test-replay build clean

# Vollständiger Qualitätscheck (vor jedem PR)
check: fmt lint test

fmt:
	black src/ tests/

lint:
	black --check src/ tests/
	mypy src/ --strict

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/core/ tests/ops/ tests/explain/ tests/data/ -v

test-replay:
	pytest tests/replay/ -v

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=50

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	find . -name "htmlcov" -exec rm -rf {} +
