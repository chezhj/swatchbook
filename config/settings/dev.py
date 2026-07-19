"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = True

# The launch configs bind 0.0.0.0 so the app can be opened on a phone over the LAN —
# this is a mobile-first design and the emulator only gets you so far. Wide open is
# fine for a local dev box; prod.py reads a real allowlist from the environment.
# Note: to test on a phone, run against built assets (`npm run build`) rather than the
# Vite dev server, whose URL is hardcoded to localhost.
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
