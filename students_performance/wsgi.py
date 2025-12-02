"""
WSGI config for students_performance project.
"""

import os
from django.core.wsgi import get_wsgi_application

# Use production settings by default
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "students_performance.production_settings"
)

application = get_wsgi_application()

# -----------------------------------------------------------
# AUTO BOOTSTRAP (Render Free Tier – No Shell Support)
# -----------------------------------------------------------
try:
    from django.core.management import call_command
    call_command("bootstrap_app")
    print("Bootstrap executed successfully.")
except Exception as e:
    print("Bootstrap skipped or failed:", e)
