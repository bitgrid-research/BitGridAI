COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: check fmt lint test test-unit test-replay build build-ci clean deploy-ha deploy-ha-restart

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
	$(COMPOSE) build

build-ci:
	docker build -t bitgrid-core:ci -f src/core/Dockerfile .
	docker build -t bitgrid-ui:ci -f src/ui/Dockerfile .

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=50

deploy-ha:
	bash scripts/deploy_ha.sh

deploy-ha-restart:
	bash scripts/deploy_ha.sh --restart

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	find . -name "htmlcov" -exec rm -rf {} +
