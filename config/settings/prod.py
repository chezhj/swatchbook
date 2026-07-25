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

# Content-Security-Policy (see web.middleware.ContentSecurityPolicyMiddleware). Static,
# no nonce: Alpine needs 'unsafe-eval' and the templates use inline style attributes, so
# a nonce would gain nothing. Google Fonts is the only external origin (base.html); every
# script/frame/connect target is locked to 'self'. img-src allows data:/blob: for the
# pre-save photo previews (URL.createObjectURL in photoTile.js).
CSP_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "img-src 'self' data: blob:; "
    "script-src 'self' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "connect-src 'self'"
)

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
DEFAULT_FROM_EMAIL = "Swatchbook<noreply@vdwaal.net>"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

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
