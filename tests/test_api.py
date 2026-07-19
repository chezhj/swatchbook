import datetime

import pytest

from catalog.models import Polish
from wearlog.models import LogEntry, LogEntryPolish

pytestmark = pytest.mark.django_db


class TestAuth:
    @pytest.mark.parametrize(
        "path",
        ["/api/polishes/", "/api/log-entries/", "/api/formulas/", "/api/brands/"],
    )
    def test_api_rejects_anonymous_requests(self, client, path):
        assert client.get(path).status_code == 403

    def test_pages_redirect_anonymous_to_login(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    def test_login_page_is_reachable_without_a_session(self, client):
        # LoginRequiredMiddleware must not lock out the login view itself.
        assert client.get("/login/").status_code == 200


class TestPolishApi:
    def test_lists_polishes(self, auth_client, polish):
        data = auth_client.get("/api/polishes/").json()
        assert data["count"] == 1
        assert data["results"][0]["name"] == "Teal No Lies"

    def test_serializer_exposes_swatch_fields(self, auth_client, polish):
        row = auth_client.get("/api/polishes/").json()["results"][0]
        assert row["hex_color"] == "#1f6e6e"
        assert sorted(row["finish_classes"]) == ["f-glitter", "f-metallic"]
        assert row["detail_url"] == f"/polish/{polish.pk}/"

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            ("formula=Glitter", ["Teal No Lies"]),
            ("formula=glitter", ["Teal No Lies"]),  # case-insensitive
            ("formula=Creme", ["Cherry Bomb"]),
            ("color=Teal", ["Teal No Lies"]),
            ("color=Teal,Red", ["Cherry Bomb", "Teal No Lies"]),
            ("brand=holo-taco", ["Teal No Lies"]),  # slug form of "Holo Taco"
            ("brand=Static Nails", ["Cherry Bomb"]),
            ("search=cherry", ["Cherry Bomb"]),
            ("formula=Glitter&color=Red", []),  # facets AND together
        ],
    )
    def test_filters(self, auth_client, polish, other_polish, query, expected):
        data = auth_client.get(f"/api/polishes/?{query}").json()
        assert sorted(r["name"] for r in data["results"]) == expected

    def test_in_collection_filter(self, auth_client, polish, other_polish):
        other_polish.in_collection = False
        other_polish.save()
        data = auth_client.get("/api/polishes/?in_collection=true").json()
        assert [r["name"] for r in data["results"]] == ["Teal No Lies"]

    def test_tag_filter(self, auth_client, polish, other_polish):
        from catalog.models import Tag

        polish.tags.add(Tag.objects.create(name="Summer"))
        data = auth_client.get("/api/polishes/?tag=summer").json()
        assert [r["name"] for r in data["results"]] == ["Teal No Lies"]

    def test_sort_by_last_used_puts_never_worn_last(self, auth_client, polish, other_polish):
        # Only `polish` has been worn; `other_polish` has last_used = NULL.
        entry = LogEntry.objects.create(date_worn=datetime.date(2026, 7, 12))
        LogEntryPolish.objects.create(log_entry=entry, polish=polish)

        names = [
            r["name"] for r in auth_client.get("/api/polishes/?sort=-last_used").json()["results"]
        ]
        assert names == ["Teal No Lies", "Cherry Bomb"]

    def test_sort_by_brand(self, auth_client, polish, other_polish):
        names = [r["name"] for r in auth_client.get("/api/polishes/?sort=brand").json()["results"]]
        assert names == ["Teal No Lies", "Cherry Bomb"]  # Holo Taco before Static Nails

    def test_unknown_sort_falls_back_to_name(self, auth_client, polish, other_polish):
        names = [
            r["name"]
            for r in auth_client.get("/api/polishes/?sort=brand__id;DROP").json()["results"]
        ]
        assert names == ["Cherry Bomb", "Teal No Lies"]

    def test_create_autogenerates_catalog_code(self, auth_client, brand):
        from catalog.models import Color, Formula

        response = auth_client.post(
            "/api/polishes/",
            {
                "name": "New One",
                "brand": brand.pk,
                "hex_color": "#123456",
                "formulas": [Formula.objects.get(name="Creme").pk],
                "colors": [Color.objects.get(name="Blue").pk],
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["catalog_code"] == "HT-001"

    def test_formula_and_color_are_required(self, auth_client, brand):
        # Per the spec's model, only `tags` is blank=True — a polish always has at
        # least one formula and one colour.
        response = auth_client.post(
            "/api/polishes/",
            {"name": "Bare", "brand": brand.pk, "hex_color": "#123456"},
            content_type="application/json",
        )
        assert response.status_code == 400
        assert set(response.json()) == {"formulas", "colors"}

    def test_rejects_a_bad_hex_colour(self, auth_client, brand):
        response = auth_client.post(
            "/api/polishes/",
            {"name": "Bad", "brand": brand.pk, "hex_color": "not-a-colour"},
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "hex_color" in response.json()

    def test_patch_updates_a_polish(self, auth_client, polish):
        response = auth_client.patch(
            f"/api/polishes/{polish.pk}/",
            {"description": "Updated"},
            content_type="application/json",
        )
        assert response.status_code == 200
        polish.refresh_from_db()
        assert polish.description == "Updated"

    def test_delete_removes_a_polish(self, auth_client, polish):
        assert auth_client.delete(f"/api/polishes/{polish.pk}/").status_code == 204
        assert Polish.objects.count() == 0


class TestVocabularyApi:
    def test_formulas_are_read_only(self, auth_client):
        assert auth_client.get("/api/formulas/").status_code == 200
        assert auth_client.post("/api/formulas/", {"name": "Nope"}).status_code == 405

    def test_colors_are_unpaginated(self, auth_client):
        data = auth_client.get("/api/colors/").json()
        assert isinstance(data, list)
        assert len(data) == 12


class TestLogApi:
    def test_creates_an_entry_with_polishes(self, auth_client, polish):
        response = auth_client.post(
            "/api/log-entries/",
            {
                "date_worn": "2026-07-12",
                "notes": "Nice",
                "entry_polishes": [{"polish": polish.pk, "role": "base"}],
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        entry = LogEntry.objects.get()
        assert entry.title == "Teal No Lies"

    def test_filters_by_polish(self, auth_client, polish, other_polish, log_entry):
        data = auth_client.get(f"/api/log-entries/?polish={other_polish.pk}").json()
        assert data["count"] == 0
        data = auth_client.get(f"/api/log-entries/?polish={polish.pk}").json()
        assert data["count"] == 1

    def test_defaults_to_newest_first(self, auth_client, polish):
        LogEntry.objects.create(date_worn=datetime.date(2026, 1, 1))
        LogEntry.objects.create(date_worn=datetime.date(2026, 6, 1))
        dates = [r["date_worn"] for r in auth_client.get("/api/log-entries/").json()["results"]]
        assert dates == ["2026-06-01", "2026-01-01"]
