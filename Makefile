# Dula — common developer commands. See docs/11-Deployment/LocalDevelopment.md.
COMPOSE = docker compose -f deploy/docker/docker-compose.dev.yml --env-file .env

.PHONY: help up down logs ps pull lint format typecheck test docs-linkcheck check-names bootstrap

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

bootstrap: ## One-time local setup hint
	@echo "1) cp .env.example .env   2) make up   3) install uv + pnpm (see docs/11-Deployment/LocalDevelopment.md)"

up: ## Start the local dev stack
	$(COMPOSE) up -d

down: ## Stop the local dev stack
	$(COMPOSE) down

logs: ## Tail dev-stack logs
	$(COMPOSE) logs -f --tail=100

ps: ## Show dev-stack status
	$(COMPOSE) ps

pull: ## Pull/verify dev-stack images (checks tags resolve)
	$(COMPOSE) pull

lint: ## Lint all code
	-uvx ruff check .
	-pnpm -r --if-present run lint

format: ## Format all code
	-uvx ruff format .
	-pnpm run format

typecheck: ## Type-check all code
	-pnpm -r --if-present run typecheck

test: ## Run all tests
	-pnpm -r --if-present run test

docs-linkcheck: ## Verify all relative Markdown links resolve (CLAUDE.md §9)
	@bash tools/check-doc-links.sh

check-names: ## Ensure old placeholder names aren't reintroduced (guardrail files allowlisted)
	@matches=$$(grep -rn --exclude-dir=.git 'Aegis\|SecLLM' . | grep -vE 'ADR-0001-product-naming\.md|CLAUDE\.md|Makefile|ci\.yml' || true); \
	if [ -n "$$matches" ]; then echo "$$matches"; echo "FAIL: forbidden names"; exit 1; else echo "naming clean"; fi
