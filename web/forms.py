from datetime import date

from django import forms
from django.forms import inlineformset_factory

from catalog.models import Brand, Collection, Color, Formula, Polish, PolishPhoto, Tag
from wearlog.models import LogEntry, LogEntryPolish, LogPhoto


class PolishForm(forms.ModelForm):
    """Add or edit a polish.

    Brand is required but a fresh install has none, so the dropdown is paired with a
    free-text field that creates one on the fly — otherwise the very first polish
    would be impossible to add without visiting the admin. Same for collection.
    Tags are comma-separated free text, matching their free-form model.
    """

    new_brand = forms.CharField(
        required=False,
        label="…or add a new brand",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Holo Taco"}),
    )
    # Collection is picked, created, or edited through a single combobox
    # (collectionCombo.js). These three fields are the plumbing it writes to: the
    # existing collection id, or the name/year for one to create on save. They're
    # hidden — the widget draws the visible search/token/edit UI over them.
    new_collection = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"x-ref": "newName"}),
    )
    new_collection_year = forms.IntegerField(
        required=False,
        min_value=1900,
        max_value=2200,
        widget=forms.HiddenInput(attrs={"x-ref": "newYear"}),
    )
    tags_text = forms.CharField(
        required=False,
        label="Tags",
        widget=forms.TextInput(attrs={"placeholder": "Comma separated, e.g. Summer, Ocean"}),
    )
    # Declared explicitly to pin assume_scheme; the default flips to https in Django 6.
    webshop_link = forms.URLField(
        required=False,
        assume_scheme="https",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    )

    class Meta:
        model = Polish
        fields = [
            "name",
            "brand",
            "collection",
            "release_year",
            "release_month",
            "release_day",
            "formulas",
            "colors",
            "description",
            "webshop_link",
            "in_collection",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "formulas": forms.CheckboxSelectMultiple,
            "colors": forms.CheckboxSelectMultiple,
            "collection": forms.HiddenInput(attrs={"x-ref": "collectionId"}),
            # The year drives the client-side "doesn't match the collection" warning
            # (releaseDate.js reads it live); month/day are plain optional numbers.
            "release_year": forms.NumberInput(
                attrs={
                    "placeholder": "YYYY",
                    "min": 1900,
                    "max": 2200,
                    "x-ref": "year",
                    "@input": "year = $event.target.value",
                }
            ),
            "release_month": forms.NumberInput(
                attrs={
                    "placeholder": "MM",
                    "min": 1,
                    "max": 12,
                    "@input": "month = $event.target.value",
                }
            ),
            "release_day": forms.NumberInput(
                attrs={
                    "placeholder": "DD",
                    "min": 1,
                    "max": 31,
                    "@input": "day = $event.target.value",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Brand may be supplied via new_brand instead, so it can't be required here;
        # clean() enforces that exactly one route is used.
        self.fields["brand"].required = False
        self.fields["brand"].queryset = Brand.objects.all()
        self.fields["collection"].queryset = Collection.objects.select_related("brand")
        self.fields["formulas"].queryset = Formula.objects.all()
        self.fields["colors"].queryset = Color.objects.all()
        # Year is the one mandatory part of the release date; month and day are optional.
        # The model field is nullable (so existing rows survived the migration) — the
        # requirement is enforced here at the form instead.
        self.fields["release_year"].required = True
        self.fields["release_year"].label = "Year"
        self.fields["release_month"].label = "Month"
        self.fields["release_day"].label = "Day"
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(t.name for t in self.instance.tags.all())

    def clean(self):
        cleaned = super().clean()
        brand = cleaned.get("brand")
        new_brand = (cleaned.get("new_brand") or "").strip()

        if not brand and not new_brand:
            self.add_error("brand", "Pick a brand or add a new one.")
        elif brand and new_brand and brand.name.lower() != new_brand.lower():
            self.add_error("new_brand", "Either pick an existing brand or add a new one, not both.")

        # Release date: month/day are optional, but each has to be in range, a day only
        # means something with a month, and month+day together have to be a real date
        # (catches 31 Feb). releaseDate.js mirrors these checks so the warning shows live;
        # this is the authoritative backstop. The collection-year mismatch is deliberately
        # *not* an error — it's a non-blocking warning surfaced client-side and on save.
        year = cleaned.get("release_year")
        month = cleaned.get("release_month")
        day = cleaned.get("release_day")

        if month is not None and not (1 <= month <= 12):
            self.add_error("release_month", "Month must be between 1 and 12.")
            month = None  # don't cascade a garbage month into the calendar check
        if day is not None and not (1 <= day <= 31):
            self.add_error("release_day", "Day must be between 1 and 31.")
            day = None

        if day and not cleaned.get("release_month"):
            self.add_error("release_day", "Add a month before a day.")
        elif month and day:
            try:
                # No year yet? Check against a leap year so a bare "29 Feb" is allowed;
                # once a real year is entered the mismatch gets caught on the next save.
                date(year or 2000, month, day)
            except ValueError:
                self.add_error("release_day", "That's not a real date.")

        return cleaned

    def save(self, commit=True):
        polish = super().save(commit=False)

        new_brand = (self.cleaned_data.get("new_brand") or "").strip()
        if new_brand:
            polish.brand, _ = Brand.objects.get_or_create(
                name__iexact=new_brand, defaults={"name": new_brand}
            )

        new_collection = (self.cleaned_data.get("new_collection") or "").strip()
        if new_collection:
            polish.collection, _ = Collection.objects.get_or_create(
                brand=polish.brand,
                name=new_collection,
                defaults={"year": self.cleaned_data.get("new_collection_year")},
            )

        if commit:
            polish.save()
            self.save_m2m()
            self._save_tags(polish)
        return polish

    def _save_tags(self, polish):
        names = [t.strip() for t in (self.cleaned_data.get("tags_text") or "").split(",")]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in names if name]
        polish.tags.set(tags)


# Photos are the swatch now, so the form opens with room for a few at once rather than
# making you save and come back for each one.
PolishPhotoFormSet = inlineformset_factory(
    Polish,
    PolishPhoto,
    fields=["image", "is_primary"],
    extra=3,
    can_delete=True,
)


class LogEntryForm(forms.ModelForm):
    class Meta:
        model = LogEntry
        fields = ["title", "date_worn", "notes"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Optional — defaults to the polishes worn"}
            ),
            "date_worn": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "How did it wear?"}),
        }
        help_texts = {
            "title": "",  # the placeholder already says it
        }


class LogEntryPolishForm(forms.ModelForm):
    """One "polish worn" row. The catalog can run to hundreds of polishes, so the
    picker is a type-to-search combobox (polishSelect.js) rather than a dropdown; the
    polish field is hidden and the combo writes the chosen id into it."""

    class Meta:
        model = LogEntryPolish
        fields = ["polish", "role"]
        widgets = {
            "polish": forms.HiddenInput(attrs={"x-ref": "polishId"}),
        }


LogEntryPolishFormSet = inlineformset_factory(
    LogEntry,
    LogEntryPolish,
    form=LogEntryPolishForm,
    extra=1,
    can_delete=True,
)

LogPhotoFormSet = inlineformset_factory(
    LogEntry,
    LogPhoto,
    fields=["image"],
    extra=1,
    can_delete=True,
)
