# Tasks API — PostgreSQL + Docker Compose (FlyRank BE-02 / A3)

A REST API for managing tasks, built with FastAPI and PostgreSQL. The application and database run in Docker containers and can be started with one command.

**Stack:** Python, FastAPI, PostgreSQL, Docker, Docker Compose

## Features

- Create, read, update, and delete tasks.
- Automatically create the database table on startup.
- Seed three example tasks only when the table is empty.
- Validate requests and return consistent error responses.
- Use parameterized SQL queries.
- Preserve database records using a named Docker volume.

## Requirements

Install Docker Desktop and ensure it is running.

## Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configuration variables:

| Variable | Purpose |
|---|---|
| `POSTGRES_PASSWORD` | Password for the PostgreSQL database |
| `DATABASE_URL` | Database connection string |

The supplied values are for local development. Do not commit your `.env` file or real credentials.

## Run the application

From the project directory, run:

```bash
docker compose up
```

Docker Compose builds the API image, starts PostgreSQL, waits for the database health check, and starts the API.

- API: http://localhost:3000
- Interactive documentation: http://localhost:3000/docs
- PostgreSQL host port: `5432`

To start in the background:

```bash
docker compose up --build -d
```

To stop the containers without deleting database data:

```bash
docker compose down
```

Start them again with `docker compose up`. The named volume preserves database records.

## API endpoints

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/tasks` | 200 | — |
| GET | `/tasks/{id}` | 200 | 404 if the task does not exist |
| POST | `/tasks` | 201 | 400 for an invalid title |
| PUT | `/tasks/{id}` | 200 | 400 for an invalid body; 404 if the task does not exist |
| DELETE | `/tasks/{id}` | 204 | 404 if the task does not exist |
| GET | `/stats` | 200 | — |

Optional filters include `GET /tasks?search=milk`, `GET /tasks?done=true`, and `GET /tasks?sort=title`.

## Test the API

List tasks:

```bash
curl -i http://localhost:3000/tasks
```

Create a task:

```bash
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Docker setup","done":false}'
```

The create request should return HTTP `201 Created`.

Check statistics:

```bash
curl -i http://localhost:3000/stats
```

## Database initialization and persistence

The application creates the `tasks` table automatically. Three example tasks are inserted only when the table is empty.

PostgreSQL stores data in the named Docker volume `taskdata`. Running `docker compose down` preserves the volume. Do not use `docker compose down -v` when testing persistence because it deletes the volume.

## Verify the database

With the containers running, connect to PostgreSQL:

```bash
docker compose exec db psql -U postgres -d tasks
```

At the PostgreSQL prompt, run:

```sql
\dt
SELECT * FROM tasks;
```

The first command lists the database tables. The second displays stored task records.

Save a screenshot of the actual PostgreSQL table and query results as `docs/postgres-tasks.png`, then commit it to the repository.

![PostgreSQL tasks table and records](docs/postgres-tasks.png)

## Project structure

```text
.
├── main.py
├── db.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .env.example
└── README.md
```

## Notes

- `.env` is excluded from Git.
- `.env.example` documents the configuration.
- SQL queries use parameterized values.
- The database persists in a named Docker volume.
