# Task Tracker API

A production-style REST API for task management built with Flask.

## Architecture

```
tasktracker-docker/
├── app/
│   ├── __init__.py      # App factory (create_app)
│   ├── config.py        # Environment-aware configuration
│   ├── models.py        # Task dataclass + enums
│   ├── storage.py       # Thread-safe in-memory store
│   ├── routes.py        # Blueprint with all route handlers
│   └── validators.py    # Input validation (decoupled from routes)
├── tests/
│   ├── conftest.py      # Shared fixtures
│   └── test_api.py      # 26 pytest tests
├── run.py               # Dev-server entry point
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/tasks` | List all tasks (supports `?status=` and `?priority=` filters) |
| GET | `/tasks/search?q=` | Search tasks by title keyword |
| POST | `/tasks` | Create a task |
| PATCH | `/tasks/<id>` | Partially update a task |
| DELETE | `/tasks/<id>` | Delete a task |

### Task schema

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `id` | string (UUID) | — | auto |
| `title` | string | max 200 chars | **required** |
| `description` | string | max 2000 chars | `""` |
| `status` | string | `pending`, `in_progress`, `completed` | `pending` |
| `priority` | string | `low`, `medium`, `high` | `medium` |
| `created_at` | ISO 8601 | — | auto |
| `updated_at` | ISO 8601 | — | auto |

## Running locally

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the dev server
python run.py
# → http://localhost:5000
```

## Running tests

```bash
pytest tests/ -v
```

## Docker

```bash
# Build and start (foreground — logs stream to terminal)
docker compose up --build

# Build and start in the background
docker compose up -d --build

# Stop containers (keeps volumes)
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild a single service without cache
docker compose build --no-cache api

# Stream logs from the running container
docker compose logs -f api

# Tail the last 50 lines then follow
docker compose logs --tail=50 -f api

# Open a shell inside the running container
docker compose exec api sh

# Check container health status
docker compose ps

# Inspect resource usage (CPU / memory)
docker stats
```

The API will be available at `http://localhost:5000`.

## Docker troubleshooting

**Port already in use (`bind: address already in use`)**

Another process is occupying port 5000. Find and stop it, or remap the port:

```bash
# Identify the process (Linux/macOS)
lsof -i :5000

# Remap to port 8080 instead — edit docker-compose.yml or override inline
docker compose run --rm -p 8080:5000 api
```

**Container exits immediately — exit code 1**

Check the full output:

```bash
docker compose logs api
```

Common causes: missing environment variable, gunicorn import error, or a syntax error introduced in `run.py` / `app/`.

**`curl: (7) Failed to connect` even though the container is running**

The container may be starting up. The `start_period` in the health check is 10 s. Wait a moment, then recheck:

```bash
docker compose ps          # look for "healthy" in the Status column
curl http://localhost:5000/health
```

**Changes to source files are not reflected**

The image is built at `docker compose up --build` time. After editing source files you must rebuild:

```bash
docker compose up --build
```

Or run the dev server locally (outside Docker) for a faster feedback loop:

```bash
python run.py              # auto-reloads on file save
```

**`ModuleNotFoundError` inside the container**

A dependency added to `requirements.txt` after the last build is missing from the image layer. Force a clean rebuild:

```bash
docker compose build --no-cache api
docker compose up
```

**Running as non-root causes a permission error**

The runtime image runs as `appuser`. If a volume mount lands files owned by root, the process cannot write them. Fix ownership on the host:

```bash
chown -R 1000:1000 ./data   # match the UID/GID of appuser
```

## Example requests

```bash
# Health check
curl http://localhost:5000/health

# Create a task (minimal)
curl -s -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "priority": "high"}' | python -m json.tool

# Create a task (all fields)
curl -s -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write unit tests",
    "description": "Cover validators and storage module",
    "status": "in_progress",
    "priority": "high"
  }' | python -m json.tool

# List all tasks
curl -s http://localhost:5000/tasks | python -m json.tool

# Filter by status
curl -s "http://localhost:5000/tasks?status=pending" | python -m json.tool

# Filter by priority
curl -s "http://localhost:5000/tasks?priority=high" | python -m json.tool

# Combine filters
curl -s "http://localhost:5000/tasks?status=pending&priority=high" | python -m json.tool

# Search tasks by title keyword
curl -s "http://localhost:5000/tasks/search?q=groceries" | python -m json.tool

# Update a task — mark complete (replace <id> with the actual UUID)
curl -s -X PATCH http://localhost:5000/tasks/<id> \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}' | python -m json.tool

# Update multiple fields at once
curl -s -X PATCH http://localhost:5000/tasks/<id> \
  -H "Content-Type: application/json" \
  -d '{"priority": "low", "description": "Done — no rush"}' | python -m json.tool

# Delete a task (returns 204 No Content)
curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:5000/tasks/<id>
```

## Flask debugging tips

**Enable debug mode with auto-reload**

Set `FLASK_DEBUG=1` before starting `run.py`. The dev server restarts on every file save and prints a full traceback in the browser on errors:

```bash
FLASK_DEBUG=1 python run.py        # Linux/macOS
$env:FLASK_DEBUG=1; python run.py  # PowerShell
```

Do **not** set this in production — debug mode exposes an interactive console.

**Print the registered route map**

```bash
python -c "from run import app; print(app.url_map)"
```

**Inspect request/response inside a route**

```python
from flask import request, current_app

@bp.route("/tasks", methods=["POST"])
def create_task():
    current_app.logger.debug("payload: %s", request.get_json())
    ...
```

Logs appear in the terminal when `FLASK_DEBUG=1` is set.

**Run the Flask shell (REPL with app context)**

```bash
flask --app run:app shell
```

From the shell you can import storage, create tasks, and inspect state without HTTP:

```python
from app.storage import TaskStore
store = TaskStore()
print(store.list_tasks())
```

**Check what gunicorn sees in Docker**

Gunicorn writes access and error logs to stdout/stderr, which Docker captures. Tail them with:

```bash
docker compose logs -f api
```

To raise the log level temporarily, edit the `CMD` in `Dockerfile`:

```
CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "--log-level=debug", "run:app"]
```

Then rebuild: `docker compose up --build`.

## HTTP status codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET / PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Validation error |
| 404 | Task not found |
| 405 | Method not allowed |
| 500 | Internal server error |
