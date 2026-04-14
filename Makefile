COMPOSE := docker compose

.PHONY: setup up down logs

setup:
	$(COMPOSE) up --build airflow-init

up:
	$(COMPOSE) up --build -d airflow-webserver airflow-scheduler

down:
	$(COMPOSE) down --volumes --remove-orphans

logs:
	$(COMPOSE) logs -f airflow-webserver airflow-scheduler postgres
