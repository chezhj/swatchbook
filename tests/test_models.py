import datetime

import pytest
from PIL import Image

from catalog.models import Color, Formula, Polish, PolishPhoto
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


class TestPolishRendering:
    def test_finish_classes_come_from_linked_formulas(self, polish):
        assert sorted(polish.finish_classes) == ["f-glitter", "f-metallic"]

    def test_is_rainbow_flags_multicolour_polishes(self, polish):
        assert polish.is_rainbow is False
        polish.colors.add(Color.objects.get(name="Rainbow"))
        assert polish.is_rainbow is True

    def test_photo_url_is_blank_when_nothing_is_uploaded(self, polish):
        # The swatch tile falls back to its placeholder on this.
        assert polish.photo_url == ""

    def test_photo_url_prefers_the_primary_photo(self, polish, big_image):
        PolishPhoto.objects.create(polish=polish, image=big_image(name="first.jpg"))
        primary = PolishPhoto.objects.create(
            polish=polish, image=big_image(name="second.jpg"), is_primary=True
        )
        assert polish.photo_url == primary.image.url


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
        assert log_entry.display_title == "Teal No Lies"

    def test_own_title_beats_the_polish_join(self, log_entry):
        log_entry.title = "Beach day mani"
        log_entry.save()
        assert log_entry.display_title == "Beach day mani"

    def test_untitled_when_nothing_linked(self, db):
        entry = LogEntry.objects.create(date_worn=datetime.date(2026, 1, 1))
        assert entry.display_title == "Untitled entry"

    def test_last_used_annotation_reflects_the_log(self, polish, log_entry):
        annotated = Polish.objects.with_last_used().get(pk=polish.pk)
        assert annotated.last_used == datetime.date(2026, 7, 12)
