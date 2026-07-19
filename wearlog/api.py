import django_filters as filters
from rest_framework import viewsets

from .models import LogEntry
from .serializers import LogEntrySerializer

LOG_SORTS = {
    "date_worn": ["date_worn"],
    "-date_worn": ["-date_worn"],
}
DEFAULT_LOG_SORT = ["-date_worn", "-id"]


class LogEntryFilter(filters.FilterSet):
    polish = filters.NumberFilter(field_name="polishes__id")
    date_from = filters.DateFilter(field_name="date_worn", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date_worn", lookup_expr="lte")

    class Meta:
        model = LogEntry
        fields = ["polish", "date_from", "date_to"]


class LogEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LogEntrySerializer
    filterset_class = LogEntryFilter

    def get_queryset(self):
        qs = LogEntry.objects.with_related().distinct()
        sort = self.request.query_params.get("sort", "")
        return qs.order_by(*LOG_SORTS.get(sort, DEFAULT_LOG_SORT))
