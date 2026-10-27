"""Repository: the only module that talks to Postgres."""
import os
import time

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

SEED_TASKS = ["Buy milk", "Learn SQL", "Push project to GitHub"]


def get_conn() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db(retries: int = 15) -> None:
    """Create the table if missing; seed 3 tasks only when it is empty.
    Retries because the db container may still be starting."""
    for attempt in range(retries):
        try:
            with get_conn() as conn:  # commits on success, rolls back on error
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id    SERIAL PRIMARY KEY,
                        title TEXT    NOT NULL,
                        done  BOOLEAN NOT NULL DEFAULT false
                    )
                    """
                )
                count = conn.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
                if count == 0:
                    with conn.cursor() as cur:
                        cur.executemany(
                            "INSERT INTO tasks (title, done) VALUES (%s, false)",
                            [(t,) for t in SEED_TASKS],
                        )
            return
        except psycopg.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def list_tasks(search=None, done=None, sort=None) -> list[dict]:
    sql, params = "SELECT * FROM tasks WHERE true", []
    if search is not None:
        sql += " AND title ILIKE %s"
        params.append(f"%{search}%")
    if done is not None:
        sql += " AND done = %s"
        params.append(done)
    sql += " ORDER BY title" if sort == "title" else " ORDER BY id"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def get_task(task_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()


def create_task(title: str, done: bool) -> dict:
    with get_conn() as conn:
        return conn.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *", (title, done)
        ).fetchone()


def update_task(task_id: int, title: str, done: bool):
    with get_conn() as conn:
        return conn.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
            (title, done, task_id),
        ).fetchone()  # None if the id doesn't exist


def delete_task(task_id: int) -> bool:
    with get_conn() as conn:
        return conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,)).rowcount > 0


def stats() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE done) AS completed FROM tasks"
        ).fetchone()
    return {"total": row["total"], "completed": row["completed"],
            "pending": row["total"] - row["completed"]}