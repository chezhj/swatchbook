import datetime

import pytest
from PIL import Image

from catalog.models import Brand, Color, Formula, Polish, PolishPhoto
from wearlog.models import LogEntry, LogPhoto

pytestmark = pytest.mark.django_db


class TestVocabularies:
    def test_seed_migration_loaded_both_lists(self):
        # Spec section 3: 9 formulas, 12 colours.
        assert Formula.objects.count() == 9
        assert Color.objects.count() == 12

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Holographic", "f-holo"),  # the mockup's CSS shortens this one
            ("Glitter", "f-glitter"),
            ("Chrome", "f-chrome"),
        ],
    )
    def test_css_class_matches_mockup(self, name, expected):
        assert Formula.objects.get(name=name).css_class == expected


class TestCatalogCode:
    def test_auto_generates_from_brand_initials(self, brand):
        polish = Polish.objects.create(brand=brand, name="Test", hex_color="#111111")
        assert polish.catalog_code == "HT-001"

    def test_single_word_brand_uses_first_two_letters(self, db):
        ilnp = Brand.objects.create(name="ILNP")
        polish = Polish.objects.create(brand=ilnp, name="Test", hex_color="#111111")
        assert polish.catalog_code == "IL-001"

    def test_sequence_increments_per_brand(self, brand):
        first = Polish.objects.create(brand=brand, name="One", hex_color="#111111")
        second = Polish.objects.create(brand=brand, name="Two", hex_color="#222222")
        assert [first.catalog_code, second.catalog_code] == ["HT-001", "HT-002"]

    def test_manual_code_is_preserved(self, brand):
        polish = Polish.objects.create(
            brand=brand, name="Manual", hex_color="#111111", catalog_code="ZZ-999"
        )
        assert polish.catalog_code == "ZZ-999"

    def test_deleting_does_not_cause_a_collision(self, brand):
        first = Polish.objects.create(brand=brand, name="One", hex_color="#111111")
        second = Polish.objects.create(brand=brand, name="Two", hex_color="#222222")
        second.delete()
        third = Polish.objects.create(brand=brand, name="Three", hex_color="#333333")
        # HT-002 is free again; HT-001 is still taken.
        assert third.catalog_code == "HT-002"
        assert first.catalog_code == "HT-001"


class TestPolishRendering:
    def test_finish_classes_come_from_linked_formulas(self, polish):
        assert sorted(polish.finish_classes) == ["f-glitter", "f-metallic"]

    def test_is_rainbow_flags_multicolour_polishes(self, polish):
        assert polish.is_rainbow is False
        polish.colors.add(Color.objects.get(name="Rainbow"))
        assert polish.is_rainbow is True


class TestPhotos:
    def test_only_one_primary_photo_survives(self, polish, big_image):
        first = PolishPhoto.objects.create(polish=polish, image=big_image(), is_primary=True)
        second = PolishPhoto.objects.create(polish=polish, image=big_image(), is_primary=True)
        first.refresh_from_db()
        assert second.is_primary is True
        assert first.is_primary is False

    def test_large_upload_is_downscaled(self, polish, big_image, settings):
        photo = PolishPhoto.objects.create(polish=polish, image=big_image(size=(3000, 2000)))
        with Image.open(photo.image.path) as img:
            # 3000x2000 scaled to a 1600 long edge, aspect ratio preserved.
            assert max(img.size) == settings.IMAGE_MAX_EDGE
            assert img.size == (1600, 1067)

    def test_png_upload_is_converted_to_jpeg(self, polish, big_image):
        photo = PolishPhoto.objects.create(
            polish=polish, image=big_image(name="shot.png", fmt="PNG")
        )
        assert photo.image.name.endswith(".jpg")

    def test_small_jpeg_is_left_alone(self, polish, big_image):
        photo = PolishPhoto.objects.create(polish=polish, image=big_image(size=(400, 300)))
        with Image.open(photo.image.path) as img:
            assert img.size == (400, 300)

    def test_log_photos_are_resized_too(self, log_entry, big_image):
        photo = LogPhoto.objects.create(log_entry=log_entry, image=big_image(size=(2400, 2400)))
        with Image.open(photo.image.path) as img:
            assert max(img.size) == 1600


class TestLogEntry:
    def test_title_joins_the_polishes_worn(self, log_entry):
        assert log_entry.title == "Teal No Lies"

    def test_untitled_when_nothing_linked(self, db):
        entry = LogEntry.objects.create(date_worn=datetime.date(2026, 1, 1))
        assert entry.title == "Untitled entry"

    def test_last_used_annotation_reflects_the_log(self, polish, log_entry):
        annotated = Polish.objects.with_last_used().get(pk=polish.pk)
        assert annotated.last_used == datetime.date(2026, 7, 12)
