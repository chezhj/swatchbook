from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.db.models import Count, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

import config
from catalog.models import Brand, Collection, Color, Formula, Polish, PolishPhoto, Tag
from wearlog.models import LogEntry, LogPhoto

from .forms import (
    LogEntryForm,
    LogEntryPolishFormSet,
    LogPhotoFormSet,
    PolishForm,
    PolishPhotoFormSet,
)


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
        # Recently-added first — matches the grid's default sort so the server paint and
        # the Alpine takeover agree.
        return (
            Polish.objects.with_related()
            .with_last_used()
            .filter(in_collection=True)
            .order_by("-created_at")
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

    def get(self, request, *args, **kwargs):
        # pk is authoritative; the slug is cosmetic. A missing or stale slug (an old
        # bookmark, or a link made before a rename) 301s to the canonical URL.
        self.object = self.get_object()
        if kwargs.get("slug") != self.object.slug:
            return redirect(self.object.get_absolute_url(), permanent=True)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_entries"] = self.object.log_entries.with_related().order_by("-date_worn")[
            :5
        ]
        return context


class PolishFormMixin:
    """Shared photo-formset wiring for the polish create/update views."""

    model = Polish
    form_class = PolishForm
    template_name = "web/polish_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object if self.object else None
        if self.request.method == "POST":
            context["photo_formset"] = PolishPhotoFormSet(
                self.request.POST, self.request.FILES, instance=instance, prefix="photos"
            )
        else:
            context["photo_formset"] = PolishPhotoFormSet(instance=instance, prefix="photos")
        return context

    def form_valid(self, form):
        photo_formset = self.get_context_data()["photo_formset"]
        if not photo_formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            photo_formset.instance = self.object
            photo_formset.save()

        messages.success(self.request, f"Saved {self.object.name}.")
        self._warn_on_year_mismatch()
        return redirect(self.get_success_url())

    def _warn_on_year_mismatch(self):
        """Backstop for the client-side check: if the release year and the collection's
        year disagree, note it after saving. Non-blocking — the save already happened."""
        collection = self.object.collection
        if (
            collection
            and collection.year
            and self.object.release_year
            and collection.year != self.object.release_year
        ):
            messages.warning(
                self.request,
                f"Heads up: release year {self.object.release_year} doesn't match the "
                f"{collection.name} collection year {collection.year}.",
            )

    def get_success_url(self):
        return self.object.get_absolute_url()


class PolishCreateView(PolishFormMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Add a polish"
        return context


class PolishUpdateView(PolishFormMixin, UpdateView):
    def get_queryset(self):
        return Polish.objects.with_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Edit polish"
        return context


class PolishDeleteView(DeleteView):
    model = Polish
    template_name = "web/polish_confirm_delete.html"
    success_url = reverse_lazy("collection")


class ComparePickerView(VocabularyMixin, ListView):
    """SCR-04. Same grid, multi-select mode."""

    template_name = "web/compare_picker.html"
    context_object_name = "polishes"

    def get_queryset(self):
        return Polish.objects.with_related().order_by("name")


class CompareResultView(TemplateView):
    """SCR-05. Two bottle swatches side by side.

    Takes up to two ?polish=<polish_id> params and shows each as catalogued —
    selecting a polish always renders that polish.
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
        context["selected"] = selected
        return context


class LogListView(VocabularyMixin, ListView):
    """SCR-06. Same split as the collection: server first paint, Alpine on change."""

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
        # The polish picker searches this list client-side, so ship it once with the
        # page (id + label) rather than paying for the full polish API per row.
        context["polish_options"] = [
            {"id": pk, "label": f"{name} — {brand}"}
            for pk, name, brand in Polish.objects.values_list("id", "name", "brand__name").order_by(
                "name"
            )
        ]
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


class AboutView(TemplateView):
    """SCR-08. Who's signed in, the collection in numbers, and the running version.

    Read-only dashboard — every figure is a live count off the catalogue, so it needs
    no storage of its own.
    """

    template_name = "web/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_active"] = "about"
        context["version"] = config.__version__

        context["stats"] = {
            "in_collection": Polish.objects.filter(in_collection=True).count(),
            "retired": Polish.objects.filter(in_collection=False).count(),
            "brands": Brand.objects.count(),
            "collections": Collection.objects.count(),
            "entries": LogEntry.objects.count(),
            # Bottle shots and worn-mani shots both count as photos of the collection.
            "photos": PolishPhoto.objects.count() + LogPhoto.objects.count(),
            "tags": Tag.objects.count(),
            "last_worn": LogEntry.objects.aggregate(d=Max("date_worn"))["d"],
        }

        context["most_worn"] = (
            Polish.objects.with_related()
            .annotate(wears=Count("log_entries"))
            .filter(wears__gt=0)
            .order_by("-wears", "name")
            .first()
        )

        # Per-colour / per-formula tallies. A polish can wear several of each, so these
        # sums run higher than the polish count — they answer "how many polishes touch
        # this colour", not "how the collection splits up". Ordered so the bar chart
        # reads big-to-small; `_max` scales the bar widths in the template.
        by_color = list(
            Color.objects.annotate(n=Count("polishes")).filter(n__gt=0).order_by("-n", "name")
        )
        by_formula = list(
            Formula.objects.annotate(n=Count("polishes")).filter(n__gt=0).order_by("-n", "name")
        )
        context["by_color"] = by_color
        context["by_formula"] = by_formula
        context["by_color_max"] = by_color[0].n if by_color else 0
        context["by_formula_max"] = by_formula[0].n if by_formula else 0

        return context


@method_decorator(login_not_required, name="dispatch")
class DevLoginView(View):
    """Dev-only shortcut: log in as a throwaway "dev" user without a password.

    Skips the login form while iterating on the UI. Guarded three ways so it can
    never authenticate anyone in production:

    1. the route is registered only when settings.DEBUG is true (web/urls.py);
    2. settings.DEV_AUTOLOGIN must also be explicitly true (defaults false);
    3. the "dev" user is created with an unusable password, so even where the
       route exists the account can't be reached through the real login form.
    """

    def get(self, request, *args, **kwargs):
        if not (settings.DEBUG and settings.DEV_AUTOLOGIN):
            raise Http404
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="dev",
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        # Explicit backend: several are configured (axes + ModelBackend), so login()
        # can't guess which authenticated this passwordless user.
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(settings.LOGIN_REDIRECT_URL)
