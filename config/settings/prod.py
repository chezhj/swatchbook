"""Production settings for the cPanel/Passenger host."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

# No default: a missing key should fail loudly at boot, not silently ship a known secret.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# The browsable API is a data-entry hazard on a live single-user site.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Error mail. Only the SMTP password is a secret and lives in .env; host, port,
# mailbox and From address are plain config. Verify the host/mailbox match what
# cPanel gives you (Email Accounts → Connect Devices shows the real values).
ADMINS = [("Admin", "h@vdwaal.net")]
SERVER_EMAIL = "swatchbook@vdwaal.net"  # From address on error mail

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.vdwaal.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "noreply@vdwaal.net"
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        # Emails unhandled 500 tracebacks to ADMINS. require_debug_false is
        # belt-and-suspenders: no mail even if DEBUG is ever flipped on here.
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "include_html": True,
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
