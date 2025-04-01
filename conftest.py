import os
import sys

import django

# Add the project root directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "MeshtasticBotManager"))


def pytest_configure():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MeshtasticBotManager.test_settings")
    django.setup()
