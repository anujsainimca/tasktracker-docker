"""
Flask configuration classes.

Select a config by passing its key to create_app(config_name).
Environment variable FLASK_ENV controls which config is active at runtime.
"""

import os


class Config:
    """Shared base configuration."""
    TESTING = False
    DEBUG = False
    # Preserve insertion order in JSON responses
    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


# Maps a string key to a config class so callers never import config classes directly.
config_map: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
