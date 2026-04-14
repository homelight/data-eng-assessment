# HomeLight Data Engineering Assessment

This repository is a lightweight local project for HomeLight data engineering pair-programming interviews.
It gives candidates a small but realistic environment with:

- Airflow for orchestration
- Postgres for storage
- Docker Compose for local setup
- A simple local seed-data DAG
- An API-driven DAG that loads Pokemon data into relational Postgres tables

The goal is to keep the project fast to boot, easy to understand, and easy to extend during an interview.

## Tech stack

- Airflow runtime image: `quay.io/astronomer/astro-runtime:13.6.0-python-3.12-slim`
- Postgres
- Docker Compose
- Make

## Project structure

- `dags/assessment_pipeline.py`: sample seed-data DAG used in the interview environment
- `dags/gotta_catch_em_all.py`: API ingestion DAG for the first 150 Pokemon
- `include/data/customers.csv`: seed data loaded by the DAG
- `Dockerfile`: custom Airflow image based on Astronomer runtime
- `docker-compose.yaml`: local Airflow + Postgres services
- `Makefile`: quick setup commands

## Prerequisites

- Docker Desktop (or equivalent Docker Engine + Compose support)
- `make`

## Quickstart

1. Initialize Airflow metadata and create the default admin user:

```bash
make setup
```

2. Start Airflow and Postgres:

```bash
make up
```

3. Open Airflow:

- URL: [http://localhost:8080](http://localhost:8080)
- Username: `admin`
- Password: `admin`

4. Trigger either `customer_postgres_pipeline` or `gotta_catch_em_all`.

5. Stop everything and remove volumes when finished:

```bash
make down
```

## Make commands

- `make setup`: builds the image, waits for Postgres, initializes the Airflow metadata database, creates the Airflow admin user, and seeds the SQL assessment tables
- `make up`: starts the Airflow webserver, Airflow scheduler, and Postgres services
- `make down`: stops containers and removes local Docker volumes
- `make logs`: tails service logs

## DAGs in the project

### `customer_postgres_pipeline`

This DAG is intentionally small and interview-friendly:

1. Creates `staging` and `analytics` schemas in Postgres
2. Loads seed customer data from `include/data/customers.csv` into `staging.customers_raw`
3. Builds `analytics.customer_summary`
4. Logs a small preview of transformed rows

### `gotta_catch_em_all`

This DAG runs daily and keeps only one active run at a time.
It reads the first 150 Pokemon from the public [PokeAPI](https://pokeapi.co/), flattens selected fields, and loads them into Postgres.

It creates and loads:

1. `analytics.pokemon`: one row per Pokemon with flattened stat columns
2. `analytics.moves`: one deduplicated row per move
3. `analytics.pokemon_moves`: many-to-many mapping between Pokemon and moves

This gives candidates a clean starting point for common interview exercises such as:

- extending a DAG
- changing transformations
- adding data quality checks
- introducing tests
- modeling downstream tables

## SQL assessment tables

Running `make setup` also creates and seeds two Postgres tables for SQL interview exercises:

- `agents`
- `transactions`

These tables are created in the default `public` schema.

## Connect to Postgres

Candidates can connect directly to the local Postgres instance from their IDE or SQL client with:

- Host: `localhost`
- Port: `5432`
- Database: `airflow`
- Username: `airflow`
- Password: `airflow`
- Schema: `public`

Example connection string:

```text
postgresql://airflow:airflow@localhost:5432/airflow
```

## Notes

- Airflow is configured with `LocalExecutor` for a simple local setup
- Postgres is available on `localhost:5432`
- The Airflow Postgres connection is preconfigured as `assessment_db`

## Troubleshooting

### `Bad Request: The CSRF tokens do not match`

If this appears in Airflow after rebuilding or restarting the local stack:

1. Run `make down`
2. Run `make setup`
3. Run `make up`
4. Refresh the browser or open Airflow in an incognito window

This usually happens when an old Airflow session cookie is still present from a previous container run.
