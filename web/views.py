from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from catalog.models import Color, Formula, Polish
from wearlog.models import LogEntry

from .forms import LogEntryForm, LogEntryPolishFormSet, LogPhotoFormSet


class VocabularyMixin:
    """Formula/colour chips for the filter sheet, straight from the lookup tables."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formulas"] = Formula.objects.all()
        context["colors"] = Color.objects.all()
        return context


class CollectionView(VocabularyMixin, ListView):
    """SCR-01 + SCR-02. Server-renders the first page; Alpine re-fetches on filter change."""

    template_name = "web/collection.html"
    context_object_name = "polishes"

    def get_queryset(self):
        return (
            Polish.objects.with_related()
            .with_last_used()
            .filter(in_collection=True)
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_count"] = context["polishes"].count()
        context["nav_active"] = "collection"
        return context


class PolishDetailView(DetailView):
    """SCR-03."""

    template_name = "web/polish_detail.html"
    context_object_name = "polish"

    def get_queryset(self):
        return Polish.objects.with_related().with_last_used()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_entries"] = self.object.log_entries.with_related().order_by("-date_worn")[
            :5
        ]
        return context


class ComparePickerView(VocabularyMixin, ListView):
    """SCR-04. Same grid, multi-select mode."""

    template_name = "web/compare_picker.html"
    context_object_name = "polishes"

    def get_queryset(self):
        return Polish.objects.with_related().order_by("name")


class CompareResultView(TemplateView):
    """SCR-05. Bottle swatch vs. a photographed mani from the log.

    Takes ?left=<polish_id> and optionally ?right=<polish_id>. When the right-hand
    polish has been worn, its most recent log entry supplies the photo column.
    """

    template_name = "web/compare_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ids = [v for v in self.request.GET.getlist("polish") if v.isdigit()][:2]
        selected = list(Polish.objects.with_related().filter(pk__in=ids))
        # Preserve the order the user picked them in.
        by_id = {str(p.pk): p for p in selected}
        selected = [by_id[i] for i in ids if i in by_id]

        context["left"] = selected[0] if selected else None
        context["right"] = selected[1] if len(selected) > 1 else None
        context["right_entry"] = None
        if context["right"]:
            context["right_entry"] = (
                context["right"].log_entries.with_related().order_by("-date_worn").first()
            )
        context["selected"] = selected
        return context


class LogListView(ListView):
    """SCR-06."""

    template_name = "web/log_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        qs = LogEntry.objects.with_related()
        polish_id = self.request.GET.get("polish")
        if polish_id and polish_id.isdigit():
            qs = qs.filter(polishes__id=int(polish_id))
        sort = self.request.GET.get("sort")
        return qs.order_by("date_worn" if sort == "date_worn" else "-date_worn").distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_active"] = "log"
        context["total_count"] = self.get_queryset().count()
        return context


class LogEntryDetailView(DetailView):
    template_name = "web/log_detail.html"
    context_object_name = "entry"

    def get_queryset(self):
        return LogEntry.objects.with_related()


class LogEntryFormMixin:
    """Shared formset wiring for the log entry create/update views."""

    model = LogEntry
    form_class = LogEntryForm
    template_name = "web/log_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object if self.object else None
        if self.request.method == "POST":
            context["polish_formset"] = LogEntryPolishFormSet(
                self.request.POST, instance=instance, prefix="polishes"
            )
            context["photo_formset"] = LogPhotoFormSet(
                self.request.POST, self.request.FILES, instance=instance, prefix="photos"
            )
        else:
            context["polish_formset"] = LogEntryPolishFormSet(instance=instance, prefix="polishes")
            context["photo_formset"] = LogPhotoFormSet(instance=instance, prefix="photos")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        polish_formset = context["polish_formset"]
        photo_formset = context["photo_formset"]

        if not (polish_formset.is_valid() and photo_formset.is_valid()):
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            polish_formset.instance = self.object
            polish_formset.save()
            photo_formset.instance = self.object
            photo_formset.save()

        messages.success(self.request, "Log entry saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("log_detail", args=[self.object.pk])


class LogEntryCreateView(LogEntryFormMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # "Log this polish" on the detail screen deep-links here with ?polish=<id>.
        polish_id = self.request.GET.get("polish")
        if polish_id and polish_id.isdigit():
            context["prefill_polish"] = get_object_or_404(Polish, pk=int(polish_id))
        context["heading"] = "New log entry"
        return context


class LogEntryUpdateView(LogEntryFormMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Edit log entry"
        return context


class LogEntryDeleteView(DeleteView):
    model = LogEntry
    template_name = "web/log_confirm_delete.html"
    success_url = reverse_lazy("log_list")


class RandomizerView(TemplateView):
    """SCR-07 placeholder. Deferred to phase 2 — see spec section 7."""

    template_name = "web/randomizer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_active"] = "random"
        return context
