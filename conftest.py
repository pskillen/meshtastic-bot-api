"""Configuration file for pytest to enable Django test settings."""

import os
import sys

import django

# Add the project root directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "MeshtasticBotManager"))


def pytest_configure():
    """Configure Django test settings for pytest."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MeshtasticBotManager.test_settings")
    django.setup()
