from django import forms
from django.forms import inlineformset_factory

from wearlog.models import LogEntry, LogEntryPolish, LogPhoto


class LogEntryForm(forms.ModelForm):
    class Meta:
        model = LogEntry
        fields = ["date_worn", "notes"]
        widgets = {
            "date_worn": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "How did it wear?"}),
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
