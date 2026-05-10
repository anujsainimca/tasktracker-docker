"""
Shared pytest fixtures.

The `client` fixture provides a Flask test client backed by the TESTING
config. The `autouse` `clear_store` fixture wipes the in-memory store
before and after every test so tests are fully isolated from each other.
"""

import pytest

from app import create_app
from app.storage import task_store


@pytest.fixture(scope="session")
def app():
    """Create a single app instance for the entire test session."""
    return create_app("testing")


@pytest.fixture
def client(app):
    """Flask test client — a new client object per test."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_store():
    """Wipe all tasks before each test; clean up after as well."""
    task_store.clear()
    yield
    task_store.clear()
