"""Add the Thermal formula to the fixed vocabulary (see 0002_seed_vocabularies)."""

from django.db import migrations

FORMULA = "Thermal"


def add(apps, schema_editor):
    Formula = apps.get_model("catalog", "Formula")
    Formula.objects.get_or_create(name=FORMULA)


def remove(apps, schema_editor):
    Formula = apps.get_model("catalog", "Formula")
    Formula.objects.filter(name=FORMULA).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_drop_hex_color_and_catalog_code")]

    operations = [migrations.RunPython(add, remove)]
