from __future__ import annotations

from pathlib import Path

import psycopg2

SQL_FILE = Path("/usr/local/airflow/include/sql/sql_assessment_seed.sql")


def main() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")
    connection = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname="airflow",
        user="airflow",
        password="airflow",
    )
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
