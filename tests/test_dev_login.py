"""Tests for the dev-only passwordless login shortcut (web.views.DevLoginView).

The route itself is registered only under DEBUG (web/urls.py), and the test suite
runs with DEBUG=False, so the view is exercised directly through RequestFactory
rather than the URL. The behaviour under each guard is what matters.
"""

import importlib

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory
from django.urls import NoReverseMatch, clear_url_caches, reverse

import config.urls
import web.urls
from web.views import DevLoginView

pytestmark = pytest.mark.django_db


def _get(path="/dev-login/"):
    """A GET request wired with the session DevLoginView.login() needs."""
    request = RequestFactory().get(path)
    SessionMiddleware(lambda r: None).process_request(request)
    request.user = AnonymousUser()
    return request


class TestDevLogin:
    def test_logs_in_a_throwaway_dev_superuser(self, settings):
        settings.DEBUG = True
        settings.DEV_AUTOLOGIN = True

        request = _get()
        response = DevLoginView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == reverse(settings.LOGIN_REDIRECT_URL)
        assert request.user.is_authenticated
        assert request.user.username == "dev"

        dev = get_user_model().objects.get(username="dev")
        assert dev.is_superuser and dev.is_staff
        # Third guard: the account can't be reached through the real login form.
        assert not dev.has_usable_password()

    def test_reuses_the_existing_dev_user(self, settings):
        settings.DEBUG = True
        settings.DEV_AUTOLOGIN = True

        DevLoginView.as_view()(_get())
        DevLoginView.as_view()(_get())

        assert get_user_model().objects.filter(username="dev").count() == 1

    def test_404s_when_flag_is_off(self, settings):
        settings.DEBUG = True
        settings.DEV_AUTOLOGIN = False

        with pytest.raises(Http404):
            DevLoginView.as_view()(_get())
        assert not get_user_model().objects.filter(username="dev").exists()

    def test_404s_when_not_debug(self, settings):
        settings.DEBUG = False
        settings.DEV_AUTOLOGIN = True

        with pytest.raises(Http404):
            DevLoginView.as_view()(_get())
        assert not get_user_model().objects.filter(username="dev").exists()

    def test_route_registration_follows_debug(self, settings):
        # The route is added at import time only under DEBUG (web/urls.py) — the
        # guarantee that keeps it out of production entirely. Reload the urlconf
        # under each DEBUG value, restoring the test default (False) afterwards so
        # no other test inherits a stale resolver.
        def _reload():
            importlib.reload(web.urls)
            importlib.reload(config.urls)
            clear_url_caches()

        try:
            settings.DEBUG = True
            _reload()
            assert reverse("dev_login") == "/dev-login/"

            settings.DEBUG = False
            _reload()
            with pytest.raises(NoReverseMatch):
                reverse("dev_login")
        finally:
            _reload()
