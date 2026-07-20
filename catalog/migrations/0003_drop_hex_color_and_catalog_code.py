"""Photos became the swatch, so a polish no longer carries a colour or a code.

Both fields are dropped outright — nothing keys off `catalog_code` (it was display
only) and `hex_color` is superseded by `PolishPhoto`. `Color.hex_color`, which tints
the filter chips, is a different field and stays.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_seed_vocabularies"),
    ]

    operations = [
        migrations.RemoveField(model_name="polish", name="hex_color"),
        migrations.RemoveField(model_name="polish", name="catalog_code"),
    ]
