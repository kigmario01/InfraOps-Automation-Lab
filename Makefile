# InfraOps Automation Lab - Makefile
.PHONY: help install lint test inventory healthcheck report audit lab-up lab-down clean

SHELL := /bin/bash
PYTHON ?= python3

help:
	@echo "InfraOps Automation Lab - Available Commands"
	@echo "============================================="
	@echo "  make install       Install Python dependencies"
	@echo "  make lint          Run Flake8 and ShellCheck linters"
	@echo "  make test          Run Python automated tests with pytest"
	@echo "  make inventory     Run Linux technical inventory (Mission 1)"
	@echo "  make healthcheck   Run Linux system health check (Mission 3)"
	@echo "  make diagnose      Run Python system diagnostics (Mission 9)"
	@echo "  make monitor       Run Python service uptime monitor (Mission 10)"
	@echo "  make report        Generate HTML & Markdown reports (Mission 12)"
	@echo "  make backup        Run automated backup script"
	@echo "  make audit         Run basic security audit"
	@echo "  make lab-up        Start Docker Sandbox test nodes"
	@echo "  make lab-down      Stop Docker Sandbox test nodes"
	@echo "  make ansible-ping  Ping all Ansible inventory hosts"
	@echo "  make clean         Clean temporary files, caches, and test artifacts"

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	@echo "--> Linting Python code with Flake8..."
	$(PYTHON) -m flake8 python tests --max-line-length=100 --extend-ignore=E203,W503 || true
	@echo "--> Checking Bash scripts syntax..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck bash/*.sh; \
	else \
		echo "shellcheck not found, checking bash syntax with -n..."; \
		for f in bash/*.sh; do bash -n "$$f" && echo "Syntax OK: $$f"; done; \
	fi

test:
	@echo "--> Running unit tests..."
	$(PYTHON) -m pytest tests -v --cov=python --cov-report=term-missing

inventory:
	@bash bash/01_server_inventory.sh

healthcheck:
	@bash bash/health_check.sh

diagnose:
	@$(PYTHON) python/infraops_cli.py diagnose

monitor:
	@$(PYTHON) python/infraops_cli.py check-endpoints

report:
	@$(PYTHON) python/infraops_cli.py report --output-dir reports

backup:
	@bash bash/backup_automation.sh --backup

audit:
	@bash bash/security_audit.sh

lab-up:
	@docker compose -f sandbox/docker-compose.lab.yml up -d
	@echo "Lab sandbox running. Target nodes accessible via SSH port 2222 and 2223."

lab-down:
	@docker compose -f sandbox/docker-compose.lab.yml down -v

ansible-ping:
	@ansible all -i ansible/inventory/hosts.ini -m ping

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov reports/*.html reports/*.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
