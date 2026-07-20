import django_filters as filters
from django.db.models import Q
from rest_framework import viewsets

from catalog.filters import filter_by_names

from .models import LogEntry
from .serializers import LogEntrySerializer

LOG_SORTS = {
    "date_worn": ["date_worn"],
    "-date_worn": ["-date_worn"],
}
DEFAULT_LOG_SORT = ["-date_worn", "-id"]


class LogEntryFilter(filters.FilterSet):
    """Mirrors the collection's query string where it makes sense for the log.

    Formula and colour reach through to the polishes worn, so "show me every
    glitter mani" works the same way it does on the collection screen.
    """

    polish = filters.NumberFilter(field_name="polishes__id")
    date_from = filters.DateFilter(field_name="date_worn", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date_worn", lookup_expr="lte")
    formula = filters.BaseInFilter(method="filter_formula")
    color = filters.BaseInFilter(method="filter_color")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = LogEntry
        fields = ["polish", "date_from", "date_to", "formula", "color"]

    def filter_formula(self, queryset, name, value):
        return filter_by_names(queryset, "polishes__formulas", value)

    def filter_color(self, queryset, name, value):
        return filter_by_names(queryset, "polishes__colors", value)

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
            | Q(notes__icontains=value)
            | Q(polishes__name__icontains=value)
            | Q(polishes__brand__name__icontains=value)
        ).distinct()


class LogEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LogEntrySerializer
    filterset_class = LogEntryFilter

    def get_queryset(self):
        qs = LogEntry.objects.with_related().distinct()
        sort = self.request.query_params.get("sort", "")
        return qs.order_by(*LOG_SORTS.get(sort, DEFAULT_LOG_SORT))
