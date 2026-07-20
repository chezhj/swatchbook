"""Load the sample collection from the mockup so the UI has real content to render.

A management command rather than a JSON fixture: M2M links read legibly and re-running
it is a no-op instead of a PK collision. It seeds no photos, so the grid renders the
placeholder tiles — add photos through the web form to see the real thing.

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

# (name, brand, formulas, colors, collection, tags, description)
POLISHES = [
    (
        "Teal No Lies",
        "Holo Taco",
        ["Metallic", "Glitter"],
        ["Teal"],
        "Holo Royalty — Shimmering Secrets",
        ["Cool-toned", "Summer", "Ocean"],
        "Deep teal metallic with smooth, full-coverage micro-flakes. "
        "Sea-like depth, one-coat finish.",
    ),
    (
        "Hit the Lights",
        "Holo Taco",
        ["Glitter"],
        ["Blue"],
        "Winter '24",
        ["Party"],
        "Navy base packed with silver scatter glitter.",
    ),
    (
        "Silent Night",
        "Holo Taco",
        ["Holographic", "Glitter"],
        ["Yellow/Gold"],
        "Winter '24",
        ["Party", "Autumn"],
        "Warm gold holo with a dense scatter.",
    ),
    (
        "Cherry Bomb",
        "Static Nails",
        ["Creme"],
        ["Red"],
        None,
        ["Bold"],
        "Classic opaque cherry red creme. Two coats, no streaks.",
    ),
    (
        "Citrus Punch",
        "ILNP",
        ["Chrome"],
        ["Orange"],
        "Summer Neons",
        ["Beachy", "Summer"],
        "Bright orange chrome with a mirror finish.",
    ),
    (
        "Moon Dust",
        "ILNP",
        ["Flakie"],
        ["White/Silver", "Neutrals"],
        None,
        ["Cozy"],
        "Sheer pearl base with iridescent flakies. Beautiful as a topper.",
    ),
    (
        "Amethyst Dream",
        "Holo Taco",
        ["Holographic"],
        ["Purple"],
        "Holo Royalty — Shimmering Secrets",
        ["Moody"],
        "Linear holographic purple. Rainbow flare in direct sun.",
    ),
    (
        "Blackout",
        "Static Nails",
        ["Chrome"],
        ["Black"],
        None,
        ["Bold", "Moody"],
        "Jet black chrome. One coat opaque.",
    ),
    (
        "Rainbow Row",
        "ILNP",
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
        for name, brand, formulas, colors, coll, tags, desc in POLISHES:
            polish, _ = Polish.objects.get_or_create(
                name=name,
                brand=brands[brand],
                defaults={
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
