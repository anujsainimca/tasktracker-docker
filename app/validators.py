"""
Input validation for task payloads.

Each function returns a (cleaned_data, error_message) tuple.
If validation passes, error_message is None; if it fails, cleaned_data is None.
Keeping validation separate from routes makes it easy to unit-test in isolation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

VALID_STATUSES = {"pending", "in_progress", "completed"}
VALID_PRIORITIES = {"low", "medium", "high"}

MAX_TITLE_LEN = 200
MAX_DESC_LEN = 2000


def validate_create_task(
    data: Any,
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Validate POST /tasks body. Unknown extra fields are silently ignored."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    # --- title (required) ---
    title = data.get("title", "")
    if not isinstance(title, str) or not title.strip():
        return None, "'title' is required and must be a non-blank string."
    title = title.strip()
    if len(title) > MAX_TITLE_LEN:
        return None, f"'title' must not exceed {MAX_TITLE_LEN} characters."

    # --- description (optional, defaults to "") ---
    description = data.get("description", "")
    if not isinstance(description, str):
        return None, "'description' must be a string."
    description = description.strip()
    if len(description) > MAX_DESC_LEN:
        return None, f"'description' must not exceed {MAX_DESC_LEN} characters."

    # --- status (optional, defaults to "pending") ---
    status = data.get("status", "pending")
    if status not in VALID_STATUSES:
        return None, f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}."

    # --- priority (optional, defaults to "medium") ---
    priority = data.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        return None, f"'priority' must be one of: {', '.join(sorted(VALID_PRIORITIES))}."

    return {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
    }, None


def validate_update_task(
    data: Any,
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Validate PATCH /tasks/<id> body. Only known fields are accepted."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    if not data:
        return None, "Request body must contain at least one field to update."

    ALLOWED = {"title", "description", "status", "priority"}
    unknown = set(data.keys()) - ALLOWED
    if unknown:
        return None, f"Unknown field(s): {', '.join(sorted(unknown))}."

    cleaned: Dict[str, str] = {}

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return None, "'title' must be a non-blank string."
        title = title.strip()
        if len(title) > MAX_TITLE_LEN:
            return None, f"'title' must not exceed {MAX_TITLE_LEN} characters."
        cleaned["title"] = title

    if "description" in data:
        description = data["description"]
        if not isinstance(description, str):
            return None, "'description' must be a string."
        description = description.strip()
        if len(description) > MAX_DESC_LEN:
            return None, f"'description' must not exceed {MAX_DESC_LEN} characters."
        cleaned["description"] = description

    if "status" in data:
        status = data["status"]
        if status not in VALID_STATUSES:
            return None, f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}."
        cleaned["status"] = status

    if "priority" in data:
        priority = data["priority"]
        if priority not in VALID_PRIORITIES:
            return None, f"'priority' must be one of: {', '.join(sorted(VALID_PRIORITIES))}."
        cleaned["priority"] = priority

    return cleaned, None
