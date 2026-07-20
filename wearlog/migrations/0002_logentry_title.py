from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wearlog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="title",
            field=models.CharField(
                blank=True,
                help_text="Optional — left blank, the entry is titled after the polishes worn.",
                max_length=150,
            ),
        ),
    ]
