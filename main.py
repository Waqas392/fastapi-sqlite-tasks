"""Tasks API — Assignment A3: same CRUD endpoints, now backed by Postgres in Docker.

Only the storage layer changed (see db.py). Routes, bodies, responses and
status codes are identical to A1/A2.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator

import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Tasks API (Postgres)", lifespan=lifespan)


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
    return error(400, "Invalid request: 'title' is required and must be a non-empty string")


@app.get("/tasks")
def list_tasks(search: str | None = None, done: bool | None = None, sort: str | None = None):
    return db.list_tasks(search, done, sort)


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = db.get_task(task_id)
    return task if task else error(404, "Task not found")


@app.post("/tasks", status_code=201)
def create_task(body: TaskIn):
    return db.create_task(body.title, body.done)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskIn):
    task = db.update_task(task_id, body.title, body.done)
    return task if task else error(404, "Task not found")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if not db.delete_task(task_id):
        return error(404, "Task not found")
    return Response(status_code=204)


@app.get("/stats")
def stats():
    return db.stats()