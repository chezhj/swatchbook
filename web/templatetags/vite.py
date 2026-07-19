"""Resolve Vite build output through its manifest.

In DEBUG the tag points at the Vite dev server (hot reload); otherwise it reads
web/static/dist/.vite/manifest.json and emits the hashed filenames. Same tag either
way, so templates never branch on environment.
"""

import json
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

MANIFEST_PATH = Path(settings.BASE_DIR) / "web" / "static" / "dist" / ".vite" / "manifest.json"


def _dev_server(request):
    # Match whatever host the page itself was requested on (localhost, 127.0.0.1, a
    # LAN IP for phone testing, ...) rather than a fixed hostname -- vite.config.js
    # binds the dev server to all interfaces so it's reachable the same way.
    host = request.get_host().rsplit(":", 1)[0] if request else "localhost"
    return f"http://{host}:5173"


@lru_cache(maxsize=1)
def _manifest():
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


@register.simple_tag(takes_context=True)
def vite_asset(context, entry="src/main.js"):
    """Emit the <script>/<link> tags for a Vite entry point."""
    if getattr(settings, "VITE_DEV_SERVER", False):
        # Note the URLs are server-root relative: vite.config.js sets base to '/' when
        # serving and '/static/dist/' only when building. If those two drift apart the
        # dev server 404s and the page renders unstyled.
        # The onerror turns "blank page, no idea why" into an actionable message when
        # VITE_DEV_MODE is on but nothing is listening on 5173.
        dev_server = _dev_server(context.get("request"))
        return mark_safe(  # noqa: S308 - fixed, non-user content
            f'<script type="module" src="{dev_server}/@vite/client"></script>'
            f'<script type="module" src="{dev_server}/{entry}" '
            f"onerror=\"console.error('Vite dev server unreachable at {dev_server} — "
            f"start it with: cd frontend \\u0026\\u0026 npm run dev, "
            f'or unset VITE_DEV_MODE to use built assets.\')"></script>'
        )

    manifest = _manifest()
    chunk = manifest.get(entry)
    if not chunk:
        # Build hasn't run yet — fail visibly in the console rather than silently
        # rendering an unstyled page with no explanation.
        return mark_safe(
            "<!-- vite: no manifest entry for "
            f"{entry}; run `npm run build` in frontend/ -->"
            '<script>console.warn("Vite assets missing - run: cd frontend && npm run build");'
            "</script>"
        )

    tags = []
    for css in chunk.get("css", []):
        tags.append(f'<link rel="stylesheet" href="{static("dist/" + css)}">')
    tags.append(f'<script type="module" src="{static("dist/" + chunk["file"])}"></script>')
    return mark_safe("".join(tags))
