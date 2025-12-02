"""
WSGI config for students_performance project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

# Default to production settings in a deployed environment.
# For local dev, you can override DJANGO_SETTINGS_MODULE manually.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "students_performance.production_settings",
)

application = get_wsgi_application()
