"""
Test settings for LOCALKAAM project.
Uses SQLite for faster testing instead of MySQL.
"""

from .settings import *
import os

# Override database to use SQLite for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Use in-memory database for tests
    }
}

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable email sending in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable logging to console during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "CRITICAL",
        },
        "accounts": {
            "handlers": ["null"],
            "level": "CRITICAL",
        },
    },
}

# Disable security settings that might interfere with tests
DEBUG = True
SECRET_KEY = "test-secret-key-not-for-production"

# Disable rate limiting for tests
RATE_LIMIT = {
    "login": {"max_attempts": 1000, "timeout": 1},
    "register": {"max_attempts": 1000, "timeout": 1},
    "password_reset": {"max_attempts": 1000, "timeout": 1},
}
