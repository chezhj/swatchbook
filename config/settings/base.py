"""Settings shared by every environment. Import from dev.py or prod.py, never directly."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "django_filters",
    "axes",
    # Local
    "catalog",
    "wearlog",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Single-user app: everything is private unless explicitly opted out with
    # @login_not_required. Saves decorating every view.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Attaches Content-Security-Policy from settings.CSP_POLICY (prod only); a no-op
    # everywhere the policy is unset, so it never touches the Vite dev server.
    "web.middleware.ContentSecurityPolicyMiddleware",
    # django-axes: must be last so it wraps the login attempt.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "web" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# django-axes throttles login brute-force. Its standalone backend must come first so a
# locked-out attempt is rejected before ModelBackend ever checks the password.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AXES_FAILURE_LIMIT = 5  # failed logins before lockout
AXES_COOLOFF_TIME = 1  # hours the lockout lasts
AXES_RESET_ON_SUCCESS = True  # a good login clears that client's failure count
# Lock on IP and on username independently. Username-based lockout still bites even if a
# proxy masks the client IP. NOTE: if this app sits behind a reverse proxy so REMOTE_ADDR
# is the proxy, configure django-ipware (AXES_IPWARE_*) to read the real client IP.
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# web/static is collected by AppDirectoriesFinder (web is an installed app),
# so it must not also be listed here or collectstatic double-discovers every
# file and warns about duplicate destination paths.

MEDIA_URL = "/media/"
# Uploaded photos. In production point DJANGO_MEDIA_ROOT at a directory OUTSIDE the
# versioned release dirs (the deploy swaps the whole app directory on every release),
# so the collection's photos persist across deploys and are never sourced from a tag.
# Left unset, it falls back to the in-repo media/ dir used in development.
MEDIA_ROOT = env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "collection"
LOGOUT_REDIRECT_URL = "login"

# Where the Django admin is mounted. Defaults to the usual admin/ for local work; in
# production set DJANGO_ADMIN_URL in .env to an unguessable path so the default /admin/
# is a 404 to the scanners that hammer it. The secret path lives in .env, never in git.
# Normalised so a value with or without slashes still resolves.
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/").strip("/") + "/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "web.pagination.SwatchbookPagination",
    "PAGE_SIZE": 60,
}

# When true, {% vite_asset %} points at the Vite dev server for hot reload instead of
# the built manifest. Set by the "Django + Vite" launch config in .vscode/launch.json.
VITE_DEV_SERVER = env.bool("VITE_DEV_MODE", default=False)

# Dev convenience: when DEBUG and this are both true, the /dev-login/ route (registered
# only under DEBUG, see web/urls.py) logs straight in as a throwaway "dev" user so the
# login form can be skipped while iterating on the UI. The dev user is created with an
# unusable password, so even where the route exists the account can't be reached through
# the real login form. Defaults false: opt in explicitly with DEV_AUTOLOGIN=true in .env.
DEV_AUTOLOGIN = env.bool("DEV_AUTOLOGIN", default=False)

# Longest edge, in pixels, that uploaded photos are resized down to. Phone photos are
# 4000px+ and would bloat MEDIA_ROOT for no visible gain at these display sizes.
IMAGE_MAX_EDGE = 1600
IMAGE_JPEG_QUALITY = 85

# Cap the non-file portion of a request (form fields, JSON) at 5 MB, well above any real
# form here. Uploaded files are exempt from this limit — Pillow's default MAX_IMAGE_PIXELS
# guard (left enabled) is what stops a decompression-bomb image, and the web server should
# cap total body size (e.g. Apache LimitRequestBody) for the file bytes themselves.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
