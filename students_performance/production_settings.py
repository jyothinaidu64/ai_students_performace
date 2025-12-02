"""
Production settings for Students Performance Management System
"""

import os
from .settings import *  # noqa
import dj_database_url

# -------------------------------------------------------------------
# Debug
# -------------------------------------------------------------------
# DEBUG env var is expected as "True"/"False" string.
DEBUG = os.environ.get("DEBUG", "False") == "True"

# -------------------------------------------------------------------
# Hosts
# -------------------------------------------------------------------
ALLOWED_HOSTS = [
    ".onrender.com",
    ".railway.app",
    ".fly.dev",
    ".pythonanywhere.com",
    "localhost",
    "127.0.0.1",
]

# You can temporarily broaden it while testing:
# ALLOWED_HOSTS = ["*"]

# -------------------------------------------------------------------
# Database
# -------------------------------------------------------------------
# DATABASE_URL is provided by Render (and others)
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# -------------------------------------------------------------------
# Static files / Whitenoise
# -------------------------------------------------------------------
# Make sure BASE_DIR is defined in your base settings.py
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Insert WhiteNoise middleware right after SecurityMiddleware
if "django.middleware.security.SecurityMiddleware" in MIDDLEWARE:
    sec_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
        MIDDLEWARE.insert(sec_index + 1, "whitenoise.middleware.WhiteNoiseMiddleware")
else:
    # Fallback: ensure Whitenoise is at least present
    if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
        MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")

# -------------------------------------------------------------------
# Media files
# -------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Tell Django it's behind a proxy that sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (uncomment after you're sure everything works over HTTPS)
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# -------------------------------------------------------------------
# Email (optional, as you had)
# -------------------------------------------------------------------
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
