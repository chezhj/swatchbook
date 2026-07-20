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
    new_collection = forms.CharField(
        required=False,
        label="…or add a new collection",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Winter '24"}),
    )
    new_collection_year = forms.IntegerField(
        required=False, label="Collection year", min_value=1900, max_value=2200
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


LogEntryPolishFormSet = inlineformset_factory(
    LogEntry,
    LogEntryPolish,
    fields=["polish", "role"],
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
