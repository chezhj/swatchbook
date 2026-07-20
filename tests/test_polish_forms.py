"""Web-UI CRUD for polishes (spec section 7, MVP "Collection CRUD")."""

import pytest

from catalog.models import Brand, Collection, Color, Formula, Polish, Tag

pytestmark = pytest.mark.django_db


def photo_management(total=0):
    return {
        "photos-TOTAL_FORMS": str(total),
        "photos-INITIAL_FORMS": "0",
        "photos-MIN_NUM_FORMS": "0",
        "photos-MAX_NUM_FORMS": "1000",
    }


def base_payload(**overrides):
    payload = {
        "name": "New Polish",
        "formulas": [Formula.objects.get(name="Creme").pk],
        "colors": [Color.objects.get(name="Blue").pk],
        "description": "",
        "webshop_link": "",
        "in_collection": "on",
        "new_brand": "",
        "new_collection": "",
        "new_collection_year": "",
        "tags_text": "",
        **photo_management(),
    }
    payload.update(overrides)
    return payload


class TestEntryPoints:
    def test_collection_screen_links_to_the_add_form(self, auth_client):
        assert "/polish/new/" in auth_client.get("/").content.decode()

    def test_empty_collection_points_somewhere_useful(self, auth_client):
        html = auth_client.get("/").content.decode()
        assert "Add your first polish" in html

    def test_detail_links_to_the_edit_form_not_the_admin(self, auth_client, polish):
        html = auth_client.get(f"/polish/{polish.pk}/").content.decode()
        assert f"/polish/{polish.pk}/edit/" in html
        assert "/admin/catalog/polish/" not in html

    def test_add_form_renders(self, auth_client):
        assert auth_client.get("/polish/new/").status_code == 200

    def test_form_leads_with_photos_and_drops_colour_and_code(self, auth_client):
        html = auth_client.get("/polish/new/").content.decode()
        assert "photo-slots" in html
        # The swatch is the photo now; neither a colour picker nor a code is asked for.
        assert 'type="color"' not in html
        assert "catalog_code" not in html
        # Photos come before the name field rather than trailing the form.
        assert html.index("photo-slots") < html.index('name="name"')


class TestCreate:
    def test_creates_with_an_existing_brand(self, auth_client, brand):
        response = auth_client.post("/polish/new/", base_payload(brand=str(brand.pk)))
        assert response.status_code == 302
        polish = Polish.objects.get(name="New Polish")
        assert polish.brand == brand
        assert [f.name for f in polish.formulas.all()] == ["Creme"]

    def test_creates_a_brand_on_the_fly(self, auth_client):
        # The first-ever polish must be addable with no brands in the database.
        assert Brand.objects.count() == 0
        response = auth_client.post("/polish/new/", base_payload(new_brand="Holo Taco"))
        assert response.status_code == 302
        polish = Polish.objects.get()
        assert polish.brand.name == "Holo Taco"

    def test_reuses_an_existing_brand_case_insensitively(self, auth_client, brand):
        auth_client.post("/polish/new/", base_payload(new_brand="holo taco"))
        assert Brand.objects.count() == 1
        assert Polish.objects.get().brand == brand

    def test_creates_a_collection_on_the_fly(self, auth_client, brand):
        response = auth_client.post(
            "/polish/new/",
            base_payload(
                brand=str(brand.pk), new_collection="Winter '24", new_collection_year="2024"
            ),
        )
        assert response.status_code == 302
        polish = Polish.objects.get()
        assert polish.collection.name == "Winter '24"
        assert polish.collection.year == 2024
        assert polish.collection.brand == brand

    def test_parses_comma_separated_tags(self, auth_client, brand):
        auth_client.post(
            "/polish/new/",
            base_payload(brand=str(brand.pk), tags_text="Summer, Ocean ,  Cool-toned"),
        )
        assert sorted(t.name for t in Polish.objects.get().tags.all()) == [
            "Cool-toned",
            "Ocean",
            "Summer",
        ]

    def test_reuses_existing_tags(self, auth_client, brand):
        Tag.objects.create(name="Summer")
        auth_client.post("/polish/new/", base_payload(brand=str(brand.pk), tags_text="Summer"))
        assert Tag.objects.filter(name="Summer").count() == 1

    def test_uploads_several_photos_at_once(self, auth_client, brand, big_image):
        # Photos are the swatch, so the form offers more than one slot up front.
        payload = base_payload(brand=str(brand.pk), **photo_management(2))
        payload["photos-0-image"] = big_image(name="a.jpg")
        payload["photos-1-image"] = big_image(name="b.jpg")
        payload["photos-1-is_primary"] = "on"

        assert auth_client.post("/polish/new/", payload).status_code == 302
        polish = Polish.objects.get()
        assert polish.photos.count() == 2
        assert polish.photos.filter(is_primary=True).count() == 1
        assert polish.photo_url == polish.photos.get(is_primary=True).image.url

    def test_uploaded_photo_is_resized(self, auth_client, brand, big_image):
        from PIL import Image

        payload = base_payload(brand=str(brand.pk), **photo_management(1))
        payload["photos-0-image"] = big_image(size=(2400, 1600))
        response = auth_client.post("/polish/new/", payload)
        assert response.status_code == 302

        photo = Polish.objects.get().photos.get()
        with Image.open(photo.image.path) as img:
            assert max(img.size) == 1600


class TestValidation:
    def test_requires_a_brand_one_way_or_another(self, auth_client):
        response = auth_client.post("/polish/new/", base_payload())
        assert response.status_code == 200  # redisplayed, not saved
        assert Polish.objects.count() == 0
        assert "Pick a brand or add a new one." in response.content.decode()

    def test_rejects_picking_and_adding_a_different_brand(self, auth_client, brand):
        response = auth_client.post(
            "/polish/new/", base_payload(brand=str(brand.pk), new_brand="Something Else")
        )
        assert response.status_code == 200
        assert Polish.objects.count() == 0

    def test_requires_formula_and_colour(self, auth_client, brand):
        payload = base_payload(brand=str(brand.pk))
        payload["formulas"] = []
        payload["colors"] = []
        response = auth_client.post("/polish/new/", payload)
        assert response.status_code == 200
        assert Polish.objects.count() == 0


class TestUpdate:
    def test_prefills_the_existing_values(self, auth_client, polish):
        polish.tags.set([Tag.objects.create(name="Ocean")])
        html = auth_client.get(f"/polish/{polish.pk}/edit/").content.decode()
        assert "Teal No Lies" in html
        assert "Ocean" in html

    def test_saves_changes(self, auth_client, polish, brand):
        response = auth_client.post(
            f"/polish/{polish.pk}/edit/",
            base_payload(brand=str(brand.pk), name="Teal No Lies v2", tags_text="Ocean"),
        )
        assert response.status_code == 302
        polish.refresh_from_db()
        assert polish.name == "Teal No Lies v2"
        assert [t.name for t in polish.tags.all()] == ["Ocean"]

    def test_can_mark_as_no_longer_owned(self, auth_client, polish, brand):
        payload = base_payload(brand=str(brand.pk), name=polish.name)
        del payload["in_collection"]  # unchecked checkbox is simply absent
        auth_client.post(f"/polish/{polish.pk}/edit/", payload)
        polish.refresh_from_db()
        assert polish.in_collection is False


class TestDelete:
    def test_confirm_page_warns_about_linked_log_entries(self, auth_client, polish, log_entry):
        html = auth_client.get(f"/polish/{polish.pk}/delete/").content.decode()
        assert "1 log entry" in html

    def test_deletes_the_polish(self, auth_client, polish):
        response = auth_client.post(f"/polish/{polish.pk}/delete/")
        assert response.status_code == 302
        assert Polish.objects.count() == 0

    def test_brand_survives_the_delete(self, auth_client, polish, brand):
        auth_client.post(f"/polish/{polish.pk}/delete/")
        assert Brand.objects.filter(pk=brand.pk).exists()


class TestCollectionUnaffected:
    def test_new_polish_appears_in_the_grid(self, auth_client, brand):
        auth_client.post("/polish/new/", base_payload(brand=str(brand.pk)))
        assert "New Polish" in auth_client.get("/").content.decode()

    def test_collection_dropdown_shows_existing_collections(self, auth_client, collection):
        html = auth_client.get("/polish/new/").content.decode()
        assert "Winter" in html
        assert Collection.objects.count() == 1
