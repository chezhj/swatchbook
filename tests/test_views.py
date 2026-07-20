import datetime

import pytest

from wearlog.models import LogEntry

pytestmark = pytest.mark.django_db


class TestSmoke:
    def test_every_route_renders(self, auth_client, polish, log_entry):
        paths = [
            "/",
            f"/polish/{polish.pk}/",
            "/compare/",
            f"/compare/result/?polish={polish.pk}",
            "/log/",
            f"/log/{log_entry.pk}/",
            "/log/new/",
            f"/log/{log_entry.pk}/edit/",
            f"/log/{log_entry.pk}/delete/",
            "/random/",
        ]
        for path in paths:
            assert auth_client.get(path).status_code == 200, path


class TestCollectionView:
    def test_photoless_polish_falls_back_to_the_placeholder_swatch(self, auth_client, polish):
        html = auth_client.get("/").content.decode()
        assert "is-empty" in html
        assert "f-glitter" in html

    def test_photo_becomes_the_swatch(self, auth_client, polish, big_image):
        from catalog.models import PolishPhoto

        photo = PolishPhoto.objects.create(polish=polish, image=big_image(), is_primary=True)
        html = auth_client.get("/").content.decode()
        assert photo.image.url in html
        # A photographed tile drops the simulated finish, so it must not be marked empty.
        assert "is-empty" not in html

    def test_hides_polishes_no_longer_owned(self, auth_client, polish, other_polish):
        other_polish.in_collection = False
        other_polish.save()
        html = auth_client.get("/").content.decode()
        assert "Teal No Lies" in html
        assert "Cherry Bomb" not in html

    def test_filter_sheet_lists_the_full_vocabulary(self, auth_client):
        html = auth_client.get("/").content.decode()
        for name in ["Creme", "Holographic", "Flakie"]:
            assert name in html
        for name in ["Pink", "Teal", "Rainbow"]:
            assert name in html


class TestCompare:
    def test_result_shows_both_selected_polishes(self, auth_client, polish, other_polish):
        response = auth_client.get(f"/compare/result/?polish={polish.pk}&polish={other_polish.pk}")
        html = response.content.decode()
        assert "Teal No Lies" in html
        assert "Cherry Bomb" in html
        assert response.context["right_entry"] is None

    def test_uses_a_logged_photo_for_the_right_column(
        self, auth_client, polish, other_polish, big_image
    ):
        from wearlog.models import LogEntryPolish, LogPhoto

        entry = LogEntry.objects.create(date_worn=datetime.date(2026, 7, 12))
        LogEntryPolish.objects.create(log_entry=entry, polish=other_polish)
        LogPhoto.objects.create(log_entry=entry, image=big_image())

        response = auth_client.get(f"/compare/result/?polish={polish.pk}&polish={other_polish.pk}")
        assert response.context["right_entry"] == entry
        assert "From log" in response.content.decode()

    def test_ignores_junk_ids(self, auth_client, polish):
        response = auth_client.get("/compare/result/?polish=abc&polish=999999")
        assert response.status_code == 200
        assert response.context["left"] is None

    def test_preserves_selection_order(self, auth_client, polish, other_polish):
        response = auth_client.get(f"/compare/result/?polish={other_polish.pk}&polish={polish.pk}")
        assert response.context["left"] == other_polish
        assert response.context["right"] == polish


class TestLogForms:
    def test_creates_an_entry_with_a_linked_polish(self, auth_client, polish):
        response = auth_client.post(
            "/log/new/",
            {
                "date_worn": "2026-07-12",
                "notes": "Test entry",
                "polishes-TOTAL_FORMS": "1",
                "polishes-INITIAL_FORMS": "0",
                "polishes-MIN_NUM_FORMS": "0",
                "polishes-MAX_NUM_FORMS": "1000",
                "polishes-0-polish": str(polish.pk),
                "polishes-0-role": "base",
                "photos-TOTAL_FORMS": "0",
                "photos-INITIAL_FORMS": "0",
                "photos-MIN_NUM_FORMS": "0",
                "photos-MAX_NUM_FORMS": "1000",
            },
        )
        assert response.status_code == 302
        entry = LogEntry.objects.get()
        assert entry.notes == "Test entry"
        assert list(entry.polishes.all()) == [polish]

    def test_own_title_is_saved_and_shown(self, auth_client, polish, log_entry):
        response = auth_client.post(
            f"/log/{log_entry.pk}/edit/",
            {
                "title": "Beach day mani",
                "date_worn": "2026-07-12",
                "notes": "",
                "polishes-TOTAL_FORMS": "0",
                "polishes-INITIAL_FORMS": "0",
                "polishes-MIN_NUM_FORMS": "0",
                "polishes-MAX_NUM_FORMS": "1000",
                "photos-TOTAL_FORMS": "0",
                "photos-INITIAL_FORMS": "0",
                "photos-MIN_NUM_FORMS": "0",
                "photos-MAX_NUM_FORMS": "1000",
            },
        )
        assert response.status_code == 302
        log_entry.refresh_from_db()
        assert log_entry.title == "Beach day mani"
        assert "Beach day mani" in auth_client.get("/log/").content.decode()

    def test_log_list_has_search_and_the_filter_sheet(self, auth_client, log_entry):
        html = auth_client.get("/log/").content.decode()
        assert "Search by title" in html
        # The sheet lists the same vocabularies as the collection's.
        for name in ["Creme", "Holographic", "Teal", "Rainbow"]:
            assert name in html

    def test_prefills_from_the_detail_screen_cta(self, auth_client, polish):
        response = auth_client.get(f"/log/new/?polish={polish.pk}")
        assert response.context["prefill_polish"] == polish
        assert "Teal No Lies" in response.content.decode()

    def test_deleting_an_entry_leaves_the_polish_alone(self, auth_client, polish, log_entry):
        response = auth_client.post(f"/log/{log_entry.pk}/delete/")
        assert response.status_code == 302
        assert LogEntry.objects.count() == 0
        polish.refresh_from_db()  # still there
