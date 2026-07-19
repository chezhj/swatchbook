"""Test settings.

Deliberately not dev.py: the debug toolbar injects itself into responses and would
both slow the suite down and break assertions on rendered HTML.
"""

from .base import *  # noqa: F403
from .base import BASE_DIR

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# In-memory database; nothing to clean up between runs.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Fast, deterministic hashing — the suite creates users constantly.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MEDIA_ROOT = BASE_DIR / "media" / "_test"

# collectstatic hasn't run in tests; skip whitenoise rather than warn on every request.
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
