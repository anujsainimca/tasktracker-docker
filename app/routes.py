"""
API route handlers.

All routes are collected in a Blueprint so they can be registered (or
swapped out) independently of the Flask app instance.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from .models import Task, TaskPriority, TaskStatus
from .storage import task_store
from .validators import validate_create_task, validate_update_task

bp = Blueprint("tasks", __name__)


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #


def _ok(data, status: int = 200):
    return jsonify(data), status


def _error(message: str, status: int):
    return jsonify({"error": message}), status


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #


@bp.route("/health", methods=["GET"])
def health():
    """Liveness probe — always returns 200 when the process is up."""
    return _ok({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@bp.route("/tasks", methods=["GET"])
def list_tasks():
    """
    Return all tasks.

    Optional query parameters:
      ?status=pending|in_progress|completed
      ?priority=low|medium|high
    """
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")

    tasks = task_store.get_all()

    if status_filter:
        tasks = [t for t in tasks if t.status.value == status_filter]
    if priority_filter:
        tasks = [t for t in tasks if t.priority.value == priority_filter]

    return _ok([t.to_dict() for t in tasks])


@bp.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task. 'title' is the only required field."""
    data = request.get_json(silent=True)
    cleaned, error = validate_create_task(data or {})
    if error:
        return _error(error, 400)

    task = Task(
        title=cleaned["title"],
        description=cleaned["description"],
        status=TaskStatus(cleaned["status"]),
        priority=TaskPriority(cleaned["priority"]),
    )
    task_store.create(task)
    return _ok(task.to_dict(), 201)


@bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    """
    Search tasks by title keyword.

    Required query parameter:
      ?q=keyword  — case-insensitive partial match against the task title
    """
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return _error("Query parameter 'q' is required.", 400)

    keyword_lower = keyword.lower()
    matches = [t for t in task_store.get_all() if keyword_lower in t.title.lower()]
    return _ok([t.to_dict() for t in matches])


@bp.route("/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id: str):
    """Partially update a task. Only supplied fields are changed."""
    task = task_store.get_by_id(task_id)
    if task is None:
        return _error(f"Task '{task_id}' not found.", 404)

    data = request.get_json(silent=True)
    cleaned, error = validate_update_task(data or {})
    if error:
        return _error(error, 400)

    if "title" in cleaned:
        task.title = cleaned["title"]
    if "description" in cleaned:
        task.description = cleaned["description"]
    if "status" in cleaned:
        task.status = TaskStatus(cleaned["status"])
    if "priority" in cleaned:
        task.priority = TaskPriority(cleaned["priority"])

    task.updated_at = datetime.now(timezone.utc)
    task_store.update(task)
    return _ok(task.to_dict())


@bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """Delete a task. Returns 204 No Content on success."""
    if not task_store.delete(task_id):
        return _error(f"Task '{task_id}' not found.", 404)
    return "", 204
