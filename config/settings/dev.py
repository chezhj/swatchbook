"""Local development settings."""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

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
