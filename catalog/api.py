from django.db.models import F
from rest_framework import viewsets

from .filters import PolishFilter
from .models import Brand, Collection, Color, Formula, Polish, Tag
from .serializers import (
    BrandSerializer,
    CollectionSerializer,
    ColorSerializer,
    FormulaSerializer,
    PolishSerializer,
    TagSerializer,
)

# Whitelist of ?sort= values. Anything else falls back to the default, so an
# arbitrary param can never reach into an unintended field.
POLISH_SORTS = {
    "name": ["name"],
    "-name": ["-name"],
    "brand": ["brand__name", "name"],
    "-brand": ["-brand__name", "name"],
    "created_at": ["created_at"],
    "-created_at": ["-created_at"],
}
DEFAULT_POLISH_SORT = ["name"]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.select_related("brand")
    serializer_class = CollectionSerializer
    filterset_fields = ["brand", "year"]


class FormulaViewSet(viewsets.ReadOnlyModelViewSet):
    """Fixed vocabulary — editable in Django admin only."""

    queryset = Formula.objects.all()
    serializer_class = FormulaSerializer
    pagination_class = None


class ColorViewSet(viewsets.ReadOnlyModelViewSet):
    """Fixed vocabulary — editable in Django admin only."""

    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class PolishViewSet(viewsets.ModelViewSet):
    serializer_class = PolishSerializer
    filterset_class = PolishFilter

    def get_queryset(self):
        # last_used is annotated unconditionally: the serializer exposes it and
        # ?sort=-last_used orders by it.
        qs = Polish.objects.with_related().with_last_used()

        sort = self.request.query_params.get("sort", "")

        # Never-worn polishes have last_used = NULL; push them to the end either way
        # rather than letting them clump at the top.
        if sort == "-last_used":
            return qs.order_by(F("last_used").desc(nulls_last=True), "name")
        if sort == "last_used":
            return qs.order_by(F("last_used").asc(nulls_last=True), "name")

        return qs.order_by(*POLISH_SORTS.get(sort, DEFAULT_POLISH_SORT))
