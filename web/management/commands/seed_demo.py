"""Load the sample collection from the mockup so the UI has real content to render.

A management command rather than a JSON fixture: catalog codes auto-generate, M2M
links read legibly, and re-running it is a no-op instead of a PK collision.

    poetry run python manage.py seed_demo
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Brand, Collection, Color, Formula, Polish, Tag
from wearlog.models import LogEntry, LogEntryPolish

BRANDS = {
    "Holo Taco": "https://holotaco.com",
    "ILNP": "https://ilnp.com",
    "Static Nails": "https://staticnails.com",
}

COLLECTIONS = [
    ("Holo Taco", "Holo Royalty — Shimmering Secrets", 2024),
    ("Holo Taco", "Winter '24", 2024),
    ("ILNP", "Summer Neons", 2025),
]

# (code, name, brand, hex, formulas, colors, collection, tags, description)
POLISHES = [
    (
        "HT-014",
        "Teal No Lies",
        "Holo Taco",
        "#1f6e6e",
        ["Metallic", "Glitter"],
        ["Teal"],
        "Holo Royalty — Shimmering Secrets",
        ["Cool-toned", "Summer", "Ocean"],
        "Deep teal metallic with smooth, full-coverage micro-flakes. "
        "Sea-like depth, one-coat finish.",
    ),
    (
        "HT-021",
        "Hit the Lights",
        "Holo Taco",
        "#2e4a8f",
        ["Glitter"],
        ["Blue"],
        "Winter '24",
        ["Party"],
        "Navy base packed with silver scatter glitter.",
    ),
    (
        "HT-022",
        "Silent Night",
        "Holo Taco",
        "#d9b23c",
        ["Holographic", "Glitter"],
        ["Yellow/Gold"],
        "Winter '24",
        ["Party", "Autumn"],
        "Warm gold holo with a dense scatter.",
    ),
    (
        "CB-003",
        "Cherry Bomb",
        "Static Nails",
        "#b3283d",
        ["Creme"],
        ["Red"],
        None,
        ["Bold"],
        "Classic opaque cherry red creme. Two coats, no streaks.",
    ),
    (
        "CP-007",
        "Citrus Punch",
        "ILNP",
        "#d9772f",
        ["Chrome"],
        ["Orange"],
        "Summer Neons",
        ["Beachy", "Summer"],
        "Bright orange chrome with a mirror finish.",
    ),
    (
        "MD-011",
        "Moon Dust",
        "ILNP",
        "#d8d5ce",
        ["Flakie"],
        ["White/Silver", "Neutrals"],
        None,
        ["Cozy"],
        "Sheer pearl base with iridescent flakies. Beautiful as a topper.",
    ),
    (
        "AD-019",
        "Amethyst Dream",
        "Holo Taco",
        "#6a4c93",
        ["Holographic"],
        ["Purple"],
        "Holo Royalty — Shimmering Secrets",
        ["Moody"],
        "Linear holographic purple. Rainbow flare in direct sun.",
    ),
    (
        "BO-002",
        "Blackout",
        "Static Nails",
        "#1b1a1f",
        ["Chrome"],
        ["Black"],
        None,
        ["Bold", "Moody"],
        "Jet black chrome. One coat opaque.",
    ),
    (
        "RR-030",
        "Rainbow Row",
        "ILNP",
        "#8a8a8a",
        ["Glitter"],
        ["Rainbow"],
        "Summer Neons",
        ["Party", "Summer"],
        "Multichrome glitter that shifts through the whole spectrum.",
    ),
]

# (date_worn, [polish names], notes)
LOG_ENTRIES = [
    (date(2026, 7, 12), ["Teal No Lies"], "Held up all week, barely any tip wear."),
    (date(2026, 6, 29), ["Hit the Lights", "Silent Night"], "Gold accent on the ring finger."),
    (date(2026, 6, 14), ["Amethyst Dream"], ""),
    (date(2026, 6, 2), ["Moon Dust", "Cherry Bomb"], "Moon Dust layered over the red."),
    (date(2026, 5, 21), ["Cherry Bomb"], "Chipped on day three."),
]


class Command(BaseCommand):
    help = "Seed the demo collection and wear log from the design mockup."

    @transaction.atomic
    def handle(self, *args, **options):
        brands = {}
        for name, website in BRANDS.items():
            brands[name], _ = Brand.objects.get_or_create(name=name, defaults={"website": website})

        collections = {}
        for brand_name, name, year in COLLECTIONS:
            collections[name], _ = Collection.objects.get_or_create(
                brand=brands[brand_name], name=name, defaults={"year": year}
            )

        polishes = {}
        for code, name, brand, hex_color, formulas, colors, coll, tags, desc in POLISHES:
            polish, _ = Polish.objects.get_or_create(
                catalog_code=code,
                defaults={
                    "name": name,
                    "brand": brands[brand],
                    "hex_color": hex_color,
                    "description": desc,
                    "collection": collections.get(coll),
                },
            )
            polish.formulas.set(Formula.objects.filter(name__in=formulas))
            polish.colors.set(Color.objects.filter(name__in=colors))
            polish.tags.set([Tag.objects.get_or_create(name=t)[0] for t in tags])
            polishes[name] = polish

        for date_worn, names, notes in LOG_ENTRIES:
            entry, created = LogEntry.objects.get_or_create(
                date_worn=date_worn, defaults={"notes": notes}
            )
            if created:
                for index, polish_name in enumerate(names):
                    LogEntryPolish.objects.create(
                        log_entry=entry,
                        polish=polishes[polish_name],
                        role="base" if index == 0 else "accent",
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Polish.objects.count()} polishes, "
                f"{Brand.objects.count()} brands, {LogEntry.objects.count()} log entries."
            )
        )
