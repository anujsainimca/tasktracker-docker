"""
Thread-safe in-memory task store.

All public methods acquire an RLock before touching shared state so the API
is safe under concurrent Flask workers (threaded=True or gunicorn thread workers).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from .models import Task


class TaskStore:
    """Simple dict-backed store protected by a reentrant lock."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # Read operations                                                      #
    # ------------------------------------------------------------------ #

    def get_all(self) -> List[Task]:
        """Return a snapshot list of all tasks (newest-first insertion order)."""
        with self._lock:
            return list(self._tasks.values())

    def get_by_id(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    # ------------------------------------------------------------------ #
    # Write operations                                                     #
    # ------------------------------------------------------------------ #

    def create(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task
            return task

    def update(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task
            return task

    def delete(self, task_id: str) -> bool:
        """Delete a task. Returns True if it existed, False otherwise."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def clear(self) -> None:
        """Remove all tasks — used by the test suite between cases."""
        with self._lock:
            self._tasks.clear()


# Module-level singleton shared across the Flask application.
task_store = TaskStore()
