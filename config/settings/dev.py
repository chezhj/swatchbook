"""Local development settings."""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

# The launch configs bind 0.0.0.0 so the app can be opened on a phone over the LAN —
# this is a mobile-first design and the emulator only gets you so far. Wide open is
# fine for a local dev box; prod.py reads a real allowlist from the environment.
# Note: to test on a phone, run against built assets (`npm run build`) rather than the
# Vite dev server, whose URL is hardcoded to localhost.
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]


def _show_toolbar(request):
    # Read settings.DEBUG live rather than closing over the constant above — the test
    # runner flips DEBUG off, and a stale closure would keep the toolbar on.
    from django.conf import settings

    return settings.DEBUG and "nodt" not in request.GET


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": _show_toolbar}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
