from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from urllib.request import Request, urlopen

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

POSTGRES_CONN_ID = "assessment_db"
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"
POKEMON_LIMIT = 150
REQUEST_HEADERS = {"User-Agent": "homelight-data-eng-assessment/1.0"}


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def build_stat_map(stats: list[dict[str, Any]]) -> dict[str, int]:
    stat_map = {
        "hp": 0,
        "attack": 0,
        "defense": 0,
        "special_attack": 0,
        "special_defense": 0,
        "speed": 0,
    }

    for stat in stats:
        stat_name = stat["stat"]["name"].replace("-", "_")
        if stat_name in stat_map:
            stat_map[stat_name] = stat["base_stat"]

    return stat_map


@dag(
    dag_id="gotta_catch_em_all",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["assessment", "pokemon", "api", "postgres"],
    description="Load the first 150 Pokemon from PokeAPI into Postgres.",
)
def gotta_catch_em_all():
    @task
    def bootstrap_database() -> None:
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        hook.run(
            """
            CREATE SCHEMA IF NOT EXISTS analytics;

            CREATE TABLE IF NOT EXISTS analytics.pokemon (
                pokemon_id INTEGER PRIMARY KEY,
                pokemon_name TEXT NOT NULL,
                pokemon_order INTEGER,
                base_experience INTEGER,
                height INTEGER,
                weight INTEGER,
                primary_type TEXT,
                hp INTEGER NOT NULL,
                attack INTEGER NOT NULL,
                defense INTEGER NOT NULL,
                special_attack INTEGER NOT NULL,
                special_defense INTEGER NOT NULL,
                speed INTEGER NOT NULL,
                processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analytics.moves (
                move_id BIGSERIAL PRIMARY KEY,
                move_name TEXT NOT NULL UNIQUE,
                move_url TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS analytics.pokemon_moves (
                pokemon_id INTEGER NOT NULL REFERENCES analytics.pokemon (pokemon_id) ON DELETE CASCADE,
                move_id BIGINT NOT NULL REFERENCES analytics.moves (move_id) ON DELETE CASCADE,
                PRIMARY KEY (pokemon_id, move_id)
            );
            """
        )

    @task
    def extract_transform_and_load() -> dict[str, int]:
        pokemon_index = fetch_json(
            f"{POKEAPI_BASE_URL}/pokemon?limit={POKEMON_LIMIT}&offset=0"
        )

        pokemon_rows: list[tuple[Any, ...]] = []
        move_name_to_url: dict[str, str] = {}
        pokemon_move_pairs: set[tuple[int, str]] = set()

        for pokemon_stub in pokemon_index["results"]:
            payload = fetch_json(pokemon_stub["url"])
            stat_map = build_stat_map(payload["stats"])
            primary_type = next(
                (
                    pokemon_type["type"]["name"]
                    for pokemon_type in sorted(payload["types"], key=lambda item: item["slot"])
                ),
                None,
            )

            pokemon_rows.append(
                (
                    payload["id"],
                    payload["name"],
                    payload["order"],
                    payload["base_experience"],
                    payload["height"],
                    payload["weight"],
                    primary_type,
                    stat_map["hp"],
                    stat_map["attack"],
                    stat_map["defense"],
                    stat_map["special-attack"],
                    stat_map["special-defense"],
                    stat_map["speed"],
                )
            )

            for move in payload["moves"]:
                move_name = move["move"]["name"]
                move_url = move["move"]["url"]
                move_name_to_url[move_name] = move_url
                pokemon_move_pairs.add((payload["id"], move_name))

        move_rows = sorted(
            (move_name, move_url) for move_name, move_url in move_name_to_url.items()
        )

        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        hook.run(
            """
            TRUNCATE TABLE analytics.pokemon_moves, analytics.moves, analytics.pokemon
            RESTART IDENTITY CASCADE;
            """
        )

        hook.insert_rows(
            table="analytics.pokemon",
            rows=sorted(pokemon_rows, key=lambda row: row[0]),
            target_fields=[
                "pokemon_id",
                "pokemon_name",
                "pokemon_order",
                "base_experience",
                "height",
                "weight",
                "primary_type",
                "hp",
                "attack",
                "defense",
                "special_attack",
                "special_defense",
                "speed",
            ],
        )

        hook.insert_rows(
            table="analytics.moves",
            rows=move_rows,
            target_fields=["move_name", "move_url"],
        )

        move_lookup_rows = hook.get_records(
            "SELECT move_id, move_name FROM analytics.moves ORDER BY move_id;"
        )
        move_id_by_name = {move_name: move_id for move_id, move_name in move_lookup_rows}

        pokemon_move_rows = sorted(
            (pokemon_id, move_id_by_name[move_name])
            for pokemon_id, move_name in pokemon_move_pairs
        )
        hook.insert_rows(
            table="analytics.pokemon_moves",
            rows=pokemon_move_rows,
            target_fields=["pokemon_id", "move_id"],
        )

        counts = {
            "pokemon_count": len(pokemon_rows),
            "move_count": len(move_rows),
            "pokemon_move_count": len(pokemon_move_rows),
        }
        logging.info("Loaded Pokemon dataset summary: %s", counts)
        return counts

    @task
    def log_results(load_summary: dict[str, int]) -> None:
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        preview_rows = hook.get_records(
            """
            SELECT
                pokemon_id,
                pokemon_name,
                primary_type,
                hp,
                attack,
                defense,
                speed
            FROM analytics.pokemon
            ORDER BY pokemon_id
            LIMIT 5;
            """
        )
        logging.info("Pokemon load summary: %s", load_summary)
        for row in preview_rows:
            logging.info("Pokemon preview row: %s", row)

    bootstrap = bootstrap_database()
    loaded = extract_transform_and_load()
    bootstrap >> loaded
    log_results(loaded)


gotta_catch_em_all()
