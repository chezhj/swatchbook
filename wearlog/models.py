from django.db import models

from catalog.imaging import resize_in_place


class LogEntryQuerySet(models.QuerySet):
    def with_related(self):
        return self.prefetch_related("photos", "entry_polishes__polish__brand")


class LogEntry(models.Model):
    date_worn = models.DateField()
    title = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional — left blank, the entry is titled after the polishes worn.",
    )
    notes = models.TextField(blank=True)
    polishes = models.ManyToManyField(
        "catalog.Polish",
        through="LogEntryPolish",
        related_name="log_entries",
    )

    objects = LogEntryQuerySet.as_manager()

    class Meta:
        ordering = ["-date_worn", "-id"]
        verbose_name_plural = "log entries"

    def __str__(self):
        return f"{self.date_worn:%d %b %Y}"

    @property
    def display_title(self):
        """The user's own title, else a summary of the mani, e.g. "Teal No Lies + Golden Hour"."""
        if self.title:
            return self.title
        names = [ep.polish.name for ep in self.entry_polishes.all()]
        if not names:
            return "Untitled entry"
        return " + ".join(names)

    @property
    def primary_photo(self):
        return self.photos.first()

    @property
    def photo_url(self):
        """URL of the list row's thumbnail, or "" when nothing was photographed."""
        photo = self.primary_photo
        return photo.image.url if photo else ""


class LogEntryPolish(models.Model):
    ROLE_CHOICES = [("base", "Base"), ("topper", "Topper"), ("accent", "Accent")]

    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name="entry_polishes")
    polish = models.ForeignKey("catalog.Polish", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="base")

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "log entry polishes"
        constraints = [
            models.UniqueConstraint(
                fields=["log_entry", "polish", "role"],
                name="unique_polish_role_per_entry",
            )
        ]

    def __str__(self):
        return f"{self.polish.name} ({self.get_role_display()})"


class LogPhoto(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="log/")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Photo from {self.log_entry}"

    def save(self, *args, **kwargs):
        resize_in_place(self.image)
        super().save(*args, **kwargs)
