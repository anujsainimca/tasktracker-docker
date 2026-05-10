"""
Entry point for running the Flask development server directly.

In production, prefer a proper WSGI server:
    gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
"""

import os

from app import create_app

# Resolve config from environment; fall back to development defaults.
env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # host="0.0.0.0" is required so the server is reachable inside Docker.
    app.run(host="0.0.0.0", port=port)
