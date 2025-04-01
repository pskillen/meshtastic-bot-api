"""Django app configuration for the NodeDB application."""

from django.apps import AppConfig


class NodeDBConfig(AppConfig):
    """Configuration class for the NodeDB Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "NodeDB"
