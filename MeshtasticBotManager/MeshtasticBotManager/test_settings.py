"""Test settings for the Meshtastic Bot Manager, using SQLite in-memory database."""

# Import all settings from the main settings file
from .settings import *  # noqa: F403, F401

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Use an in-memory database for tests
    }
}
