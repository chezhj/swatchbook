"""Tests for web.middleware."""

import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.test import RequestFactory

from web.middleware import ContentSecurityPolicyMiddleware


class TestContentSecurityPolicyMiddleware:
    def test_adds_header_when_policy_is_configured(self, settings):
        settings.CSP_POLICY = "default-src 'self'"
        mw = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
        response = mw(RequestFactory().get("/"))
        assert response["Content-Security-Policy"] == "default-src 'self'"

    def test_does_not_clobber_a_header_a_view_already_set(self, settings):
        settings.CSP_POLICY = "default-src 'self'"

        def view(request):
            resp = HttpResponse("ok")
            resp["Content-Security-Policy"] = "default-src 'none'"
            return resp

        response = ContentSecurityPolicyMiddleware(view)(RequestFactory().get("/"))
        assert response["Content-Security-Policy"] == "default-src 'none'"

    def test_disables_itself_when_no_policy(self, settings):
        settings.CSP_POLICY = ""
        with pytest.raises(MiddlewareNotUsed):
            ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
