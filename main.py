"""Tasks API — Assignment A2: same CRUD endpoints as A1, now backed by SQLite.

Only the storage layer changed. The routes keep the same URLs, request bodies,
responses and status codes as the in-memory version.
"""
import os
import sqlite3
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator

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


def row_to_task(row: sqlite3.Row) -> dict:
    # SQLite stores booleans as 0/1; the API keeps returning true/false like A1.
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# ------------------------------------------------------------------------- app
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tasks API (SQLite)", lifespan=lifespan)


class TaskIn(BaseModel):
    title: str
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    # FastAPI defaults to 422; the assignment (and A1) use 400 for invalid bodies.
    return error(400, "Invalid request: 'title' is required and must be a non-empty string")


@app.get("/tasks")
def list_tasks(search: str | None = None, done: bool | None = None, sort: str | None = None):
    # Optional extras: ?search=milk  ?done=true  ?sort=title — all done in SQL.
    sql, params = "SELECT * FROM tasks WHERE 1=1", []
    if search is not None:
        sql += " AND title LIKE ?"
        params.append(f"%{search}%")
    if done is not None:
        sql += " AND done = ?"
        params.append(int(done))
    sql += " ORDER BY title" if sort == "title" else " ORDER BY id"
    with closing(get_conn()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return error(404, "Task not found")
    return row_to_task(row)


@app.post("/tasks", status_code=201)
def create_task(body: TaskIn):
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", (body.title, int(body.done))
            )
            task_id = cur.lastrowid  # the database hands out the id
    return {"id": task_id, "title": body.title, "done": body.done}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskIn):
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (body.title, int(body.done), task_id),
            )
        if cur.rowcount == 0:
            return error(404, "Task not found")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cur.rowcount == 0:
        return error(404, "Task not found")
    return Response(status_code=204)


@app.get("/stats")
def stats():
    # Optional extra: let SQL do the counting.
    with closing(get_conn()) as conn:
        total, = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()
        completed, = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()
    return {"total": total, "completed": completed, "pending": total - completed}
