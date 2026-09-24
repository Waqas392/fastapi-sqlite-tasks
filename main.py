"""Tasks API — Assignment A2: same CRUD endpoints as A1, now backed by SQLite."""
import os
import sqlite3
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI

# The database file lives next to this script and is created automatically.
DB_PATH = Path(os.getenv("TASKS_DB", Path(__file__).parent / "tasks.db"))

SEED_TASKS = ["Buy milk", "Learn SQL", "Push project to GitHub"]


# ---------------------------------------------------------------- storage layer
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create the table if missing; seed 3 tasks only when the table is empty."""
    with closing(get_conn()) as conn:
        with conn:  # one transaction: commits on success, rolls back on error
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id    INTEGER PRIMARY KEY,
                    title TEXT    NOT NULL,
                    done  BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
            (count,) = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()
            if count == 0:
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, 0)",
                    [(t,) for t in SEED_TASKS],
                )


# ------------------------------------------------------------------------- app
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tasks API (SQLite)", lifespan=lifespan)
