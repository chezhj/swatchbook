import re

from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

from .imaging import resize_in_place

HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{6})$",
    message="Enter a colour as #rrggbb, e.g. #1f6e6e.",
)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def code_prefix(self):
        """Initials used to build catalog codes: "Holo Taco" -> "HT"."""
        words = re.findall(r"[A-Za-z0-9]+", self.name)
        if not words:
            return "XX"
        if len(words) == 1:
            return words[0][:2].upper()
        return "".join(w[0] for w in words[:3]).upper()


class Collection(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["brand__name", "-year", "name"]
        constraints = [
            models.UniqueConstraint(fields=["brand", "name"], name="unique_collection_per_brand")
        ]

    def __str__(self):
        return f"{self.name} ({self.year})" if self.year else self.name


class Formula(models.Model):
    """Fixed vocabulary, seeded via data migration — see spec section 3."""

    name = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def css_class(self):
        """Finish class the mockup's swatch CSS keys off, e.g. "f-holo"."""
        slug = slugify(self.name)
        # The mockup shortens this one; everything else maps straight through.
        if slug == "holographic":
            slug = "holo"
        return f"f-{slug}"


class Color(models.Model):
    """Fixed vocabulary, seeded via data migration — see spec section 3."""

    name = models.CharField(max_length=30, unique=True)
    hex_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[HEX_COLOR_VALIDATOR],
        help_text="Dot colour for this family's filter chip.",
    )

    class Meta:
        ordering = ["id"]  # seeded in the spec's order, which is a deliberate colour wheel

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Free-form, user-created."""

    name = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PolishQuerySet(models.QuerySet):
    def with_related(self):
        """Prefetch everything a swatch grid cell renders. The grid is the hot path."""
        return self.select_related("brand", "collection").prefetch_related(
            "formulas", "colors", "tags", "photos"
        )

    def with_last_used(self):
        return self.annotate(last_used=models.Max("log_entries__date_worn"))


class Polish(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="polishes")
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="polishes",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    webshop_link = models.URLField(blank=True)
    hex_color = models.CharField(
        max_length=7,
        validators=[HEX_COLOR_VALIDATOR],
        default="#8a8a8a",
        help_text="Base swatch colour, e.g. #1f6e6e. Finish effects layer on top of this.",
    )
    formulas = models.ManyToManyField(Formula, related_name="polishes")
    colors = models.ManyToManyField(Color, related_name="polishes")
    tags = models.ManyToManyField(Tag, blank=True, related_name="polishes")
    catalog_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Leave blank to auto-generate from the brand, e.g. HT-014.",
    )
    in_collection = models.BooleanField(
        default=True,
        help_text="Unticked means it was owned once but no longer is.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PolishQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "polishes"

    def __str__(self):
        return f"{self.name} — {self.brand.name}"

    def save(self, *args, **kwargs):
        if not self.catalog_code:
            self.catalog_code = self._generate_catalog_code()
        super().save(*args, **kwargs)

    def _generate_catalog_code(self):
        """Next free <PREFIX>-<NNN> for this brand.

        Scans existing codes rather than counting rows, so deleting a polish never
        causes the next one to collide with a code that is still in use.
        """
        prefix = self.brand.code_prefix
        existing = Polish.objects.filter(catalog_code__startswith=f"{prefix}-").values_list(
            "catalog_code", flat=True
        )
        used = set()
        for code in existing:
            suffix = code[len(prefix) + 1 :]
            if suffix.isdigit():
                used.add(int(suffix))
        seq = 1
        while seq in used:
            seq += 1
        return f"{prefix}-{seq:03d}"

    @property
    def finish_classes(self):
        """CSS classes for the swatch's finish overlays, derived from the linked formulas."""
        return [f.css_class for f in self.formulas.all()]

    @property
    def is_rainbow(self):
        """Multi-colour polishes render as a conic gradient, ignoring hex_color."""
        return any(c.name == "Rainbow" for c in self.colors.all())

    @property
    def primary_photo(self):
        photos = list(self.photos.all())
        if not photos:
            return None
        return next((p for p in photos if p.is_primary), photos[0])


class PolishPhoto(models.Model):
    polish = models.ForeignKey(Polish, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="polishes/")
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Photo of {self.polish.name}"

    def save(self, *args, **kwargs):
        resize_in_place(self.image)
        super().save(*args, **kwargs)
        if self.is_primary:
            # Exactly one primary per polish.
            PolishPhoto.objects.filter(polish=self.polish).exclude(pk=self.pk).update(
                is_primary=False
            )
