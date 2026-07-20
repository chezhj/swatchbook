import io

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from catalog.models import Brand, Collection, Color, Formula, Polish
from wearlog.models import LogEntry, LogEntryPolish


@pytest.fixture(autouse=True)
def isolated_media(settings, tmp_path):
    """Keep uploaded test files out of the real media/ directory."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pw-for-tests-only")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="Holo Taco")


@pytest.fixture
def other_brand(db):
    return Brand.objects.create(name="Static Nails")


@pytest.fixture
def collection(brand):
    return Collection.objects.create(brand=brand, name="Winter", year=2024)


@pytest.fixture
def polish(brand):
    p = Polish.objects.create(brand=brand, name="Teal No Lies")
    p.formulas.set(Formula.objects.filter(name__in=["Metallic", "Glitter"]))
    p.colors.set(Color.objects.filter(name="Teal"))
    return p


@pytest.fixture
def other_polish(other_brand):
    p = Polish.objects.create(brand=other_brand, name="Cherry Bomb")
    p.formulas.set(Formula.objects.filter(name="Creme"))
    p.colors.set(Color.objects.filter(name="Red"))
    return p


@pytest.fixture
def log_entry(polish):
    import datetime

    entry = LogEntry.objects.create(date_worn=datetime.date(2026, 7, 12))
    LogEntryPolish.objects.create(log_entry=entry, polish=polish, role="base")
    return entry


@pytest.fixture
def big_image():
    """A 3000px JPEG, standing in for a phone photo."""

    def _make(name="photo.jpg", size=(3000, 2000), fmt="JPEG"):
        buffer = io.BytesIO()
        Image.new("RGB", size, (120, 60, 90)).save(buffer, format=fmt)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")

    return _make
