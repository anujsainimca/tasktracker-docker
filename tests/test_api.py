"""
pytest test suite for the Task Management REST API.

Coverage targets:
  - Health endpoint
  - Task listing (empty store, populated store, query filters)
  - Task creation (happy path, defaults, validation failures)
  - Task update   (happy path, partial update, validation failures, 404)
  - Task deletion (happy path, 404)
  - Edge cases    (title length limit, no JSON body, unknown fields)
"""

from __future__ import annotations

import json


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #


def post_task(client, **kwargs):
    """POST /tasks with the given JSON payload. Returns the response."""
    payload = {"title": "Default Task", **kwargs}
    return client.post("/tasks", json=payload)


def get_created_id(client, **kwargs) -> str:
    """Create a task and return its ID."""
    resp = post_task(client, **kwargs)
    return resp.get_json()["id"]


# ------------------------------------------------------------------ #
# 1. Health endpoint                                                  #
# ------------------------------------------------------------------ #


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_response_shape(client):
    data = client.get("/health").get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data


# ------------------------------------------------------------------ #
# 2. List tasks                                                       #
# ------------------------------------------------------------------ #


def test_list_tasks_empty_store(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_tasks_returns_all_created(client):
    post_task(client, title="Task A")
    post_task(client, title="Task B")
    data = client.get("/tasks").get_json()
    titles = {t["title"] for t in data}
    assert titles == {"Task A", "Task B"}


def test_list_tasks_filter_by_status(client):
    post_task(client, title="Pending one", status="pending")
    post_task(client, title="Done one", status="completed")
    data = client.get("/tasks?status=completed").get_json()
    assert len(data) == 1
    assert data[0]["title"] == "Done one"


def test_list_tasks_filter_by_priority(client):
    post_task(client, title="High prio", priority="high")
    post_task(client, title="Low prio", priority="low")
    data = client.get("/tasks?priority=high").get_json()
    assert len(data) == 1
    assert data[0]["priority"] == "high"


# ------------------------------------------------------------------ #
# 3. Create task                                                       #
# ------------------------------------------------------------------ #


def test_create_task_returns_201(client):
    resp = post_task(client, title="New task")
    assert resp.status_code == 201


def test_create_task_response_shape(client):
    resp = post_task(client, title="Shape test")
    data = resp.get_json()
    for key in ("id", "title", "description", "status", "priority", "created_at", "updated_at"):
        assert key in data, f"Missing key: {key}"


def test_create_task_applies_defaults(client):
    data = post_task(client, title="Defaults").get_json()
    assert data["status"] == "pending"
    assert data["priority"] == "medium"
    assert data["description"] == ""


def test_create_task_accepts_all_fields(client):
    resp = post_task(
        client,
        title="Full task",
        description="A description",
        status="in_progress",
        priority="high",
    )
    data = resp.get_json()
    assert data["title"] == "Full task"
    assert data["description"] == "A description"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_create_task_missing_title_returns_400(client):
    resp = client.post("/tasks", json={"description": "No title here"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_task_blank_title_returns_400(client):
    resp = post_task(client, title="   ")
    assert resp.status_code == 400


def test_create_task_invalid_status_returns_400(client):
    resp = post_task(client, title="Bad status", status="done")
    assert resp.status_code == 400


def test_create_task_invalid_priority_returns_400(client):
    resp = post_task(client, title="Bad priority", priority="urgent")
    assert resp.status_code == 400


def test_create_task_title_too_long_returns_400(client):
    resp = post_task(client, title="x" * 201)
    assert resp.status_code == 400


def test_create_task_no_body_returns_400(client):
    # Sending no JSON body at all
    resp = client.post("/tasks", content_type="application/json", data="")
    assert resp.status_code == 400


# ------------------------------------------------------------------ #
# 4. Update task                                                       #
# ------------------------------------------------------------------ #


def test_update_task_returns_200(client):
    task_id = get_created_id(client, title="Original")
    resp = client.patch(f"/tasks/{task_id}", json={"title": "Updated"})
    assert resp.status_code == 200


def test_update_task_partial_fields(client):
    task_id = get_created_id(client, title="Partial", priority="low")
    resp = client.patch(f"/tasks/{task_id}", json={"status": "completed"})
    data = resp.get_json()
    # Changed field
    assert data["status"] == "completed"
    # Untouched fields must be preserved
    assert data["title"] == "Partial"
    assert data["priority"] == "low"


def test_update_task_all_fields(client):
    task_id = get_created_id(client, title="Original")
    payload = {"title": "New", "description": "Desc", "status": "in_progress", "priority": "high"}
    data = client.patch(f"/tasks/{task_id}", json=payload).get_json()
    assert data["title"] == "New"
    assert data["description"] == "Desc"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_update_task_not_found_returns_404(client):
    resp = client.patch("/tasks/nonexistent-id", json={"title": "X"})
    assert resp.status_code == 404


def test_update_task_empty_body_returns_400(client):
    task_id = get_created_id(client, title="Task")
    resp = client.patch(f"/tasks/{task_id}", json={})
    assert resp.status_code == 400


def test_update_task_unknown_field_returns_400(client):
    task_id = get_created_id(client, title="Task")
    resp = client.patch(f"/tasks/{task_id}", json={"colour": "red"})
    assert resp.status_code == 400
    assert "Unknown field" in resp.get_json()["error"]


def test_update_task_invalid_status_returns_400(client):
    task_id = get_created_id(client, title="Task")
    resp = client.patch(f"/tasks/{task_id}", json={"status": "archived"})
    assert resp.status_code == 400


def test_update_task_updates_updated_at(client):
    task_id = get_created_id(client, title="Timing")
    original_updated_at = client.get("/tasks").get_json()[0]["updated_at"]

    # Patch the task
    patched = client.patch(f"/tasks/{task_id}", json={"title": "Timed"}).get_json()
    assert patched["updated_at"] >= original_updated_at


# ------------------------------------------------------------------ #
# 5. Delete task                                                       #
# ------------------------------------------------------------------ #


def test_delete_task_returns_204(client):
    task_id = get_created_id(client, title="To delete")
    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204
    assert resp.data == b""


def test_delete_task_removes_from_store(client):
    task_id = get_created_id(client, title="Gone")
    client.delete(f"/tasks/{task_id}")
    tasks = client.get("/tasks").get_json()
    assert all(t["id"] != task_id for t in tasks)


def test_delete_task_not_found_returns_404(client):
    resp = client.delete("/tasks/does-not-exist")
    assert resp.status_code == 404


def test_delete_task_then_get_returns_404(client):
    task_id = get_created_id(client, title="Delete then get")
    client.delete(f"/tasks/{task_id}")
    # After deletion, PATCH should also 404
    resp = client.patch(f"/tasks/{task_id}", json={"title": "Ghost"})
    assert resp.status_code == 404
