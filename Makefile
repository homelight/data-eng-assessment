COMPOSE := docker compose

.DEFAULT_GOAL := help

.PHONY: help setup up down logs

help: ## Show available make targets
	@awk 'BEGIN {FS = ":.*## "; printf "\nAvailable commands:\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-10s %s\n", $$1, $$2} END {printf "\n"}' $(MAKEFILE_LIST)

setup: ## Build image and initialize local services
	$(COMPOSE) up --build airflow-init

up: ## Start Airflow, Postgres, and JupyterLab
	$(COMPOSE) up --build -d airflow-webserver airflow-scheduler jupyter

down: ## Stop containers and remove volumes
	$(COMPOSE) down --volumes --remove-orphans

logs: ## Tail Airflow, Postgres, and JupyterLab logs
	$(COMPOSE) logs -f airflow-webserver airflow-scheduler postgres jupyter
