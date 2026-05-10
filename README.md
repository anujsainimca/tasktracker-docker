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
# Build and start
docker compose up --build

# Run in the background
docker compose up -d --build

# Stop
docker compose down
```

The API will be available at `http://localhost:5000`.

## Example requests

```bash
# Health check
curl http://localhost:5000/health

# Create a task
curl -s -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "priority": "high"}'

# List tasks
curl http://localhost:5000/tasks

# Filter by status
curl "http://localhost:5000/tasks?status=pending"

# Update a task (replace <id> with the actual UUID)
curl -s -X PATCH http://localhost:5000/tasks/<id> \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Delete a task
curl -s -X DELETE http://localhost:5000/tasks/<id>
```

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
