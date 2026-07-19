"""cPanel/Passenger entrypoint.

Passenger imports this module from the app root and looks for `application`.
Point the cPanel "Application startup file" at this file and set
DJANGO_SETTINGS_MODULE=config.settings.prod in the app's environment (or in .env).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
