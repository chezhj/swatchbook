"""Seed the fixed Formula and Color vocabularies from spec section 3.

These live in real tables (not TextChoices) so a polish can carry several of each via
M2M, and so the lists stay editable from Django admin without a code change.
"""

from django.db import migrations

FORMULAS = [
    "Creme",
    "Holographic",
    "Jelly",
    "Glitter",
    "Magnetic",
    "Shimmer",
    "Metallic",
    "Chrome",
    "Flakie",
]

# Hex values are the filter-chip dots from the mockup's COLORS array.
COLORS = [
    ("Pink", "#c2447a"),
    ("Red", "#b3283d"),
    ("Orange", "#d9772f"),
    ("Yellow/Gold", "#d9b23c"),
    ("Green", "#4c7a5e"),
    ("Teal", "#1f6e6e"),
    ("Blue", "#2e4a8f"),
    ("Purple", "#6a4c93"),
    ("Neutrals", "#b9a99a"),
    ("White/Silver", "#d8d5ce"),
    ("Black", "#1b1a1f"),
    ("Rainbow", ""),  # rendered as a conic gradient, not a flat colour
]


def seed(apps, schema_editor):
    Formula = apps.get_model("catalog", "Formula")
    Color = apps.get_model("catalog", "Color")

    for name in FORMULAS:
        Formula.objects.get_or_create(name=name)

    for name, hex_color in COLORS:
        Color.objects.get_or_create(name=name, defaults={"hex_color": hex_color})


def unseed(apps, schema_editor):
    Formula = apps.get_model("catalog", "Formula")
    Color = apps.get_model("catalog", "Color")

    Formula.objects.filter(name__in=FORMULAS).delete()
    Color.objects.filter(name__in=[c[0] for c in COLORS]).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
