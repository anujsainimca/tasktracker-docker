"""
Flask application factory.

Calling create_app() returns a fully-configured Flask instance.
Accepting a config_name argument lets tests spin up a TESTING-flavoured
app without any global state leaking between test runs.
"""

from __future__ import annotations

from flask import Flask, jsonify

from .config import config_map
from .routes import bp as tasks_bp


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # ------------------------------------------------------------------ #
    # Blueprints                                                           #
    # ------------------------------------------------------------------ #
    app.register_blueprint(tasks_bp)

    # ------------------------------------------------------------------ #
    # Global error handlers                                                #
    # ------------------------------------------------------------------ #

    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        return jsonify({"error": "Internal server error."}), 500

    return app
