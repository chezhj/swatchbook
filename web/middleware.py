"""Custom middleware."""

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed


class ContentSecurityPolicyMiddleware:
    """Attach a static Content-Security-Policy from ``settings.CSP_POLICY``.

    The policy is a fixed string, not a per-request nonce: Alpine evaluates its
    directives through ``Function()`` (so ``script-src`` must keep ``'unsafe-eval'``)
    and the templates lean on inline ``style="…"`` attributes (which only
    ``style-src 'unsafe-inline'`` allows — nonces don't cover style attributes), so a
    nonce would buy nothing. What the policy *does* buy is origin locking: scripts,
    frames, objects and XHR are pinned to ``'self'`` (+ Google Fonts for CSS/fonts),
    so an injected ``<script src>``, iframe, or exfil endpoint is refused.

    Left unset (dev/test) the middleware removes itself, so it never fights the Vite
    dev server's HMR websocket or inline bootstrap.
    """

    def __init__(self, get_response):
        self.policy = getattr(settings, "CSP_POLICY", "")
        if not self.policy:
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self.policy)
        return response
