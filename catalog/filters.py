import django_filters as filters
from django.db.models import Q

from .models import Polish


def filter_by_names(queryset, relation, values):
    """OR the values against `<relation>__name`, case-insensitively.

    slugify-tolerant: "holo-taco" should match "Holo Taco". An OR of iexact rather
    than a built regex — user input never becomes a pattern. Shared with the wear
    log's filters, which face the same vocabularies through their polishes.
    """
    if not values:
        return queryset
    cleaned = [v.replace("-", " ").strip() for v in values if v.strip()]
    if not cleaned:
        return queryset
    q = Q()
    for value in cleaned:
        q |= Q(**{f"{relation}__name__iexact": value})
    return queryset.filter(q).distinct()


class PolishFilter(filters.FilterSet):
    """Filters matching the query string in spec section 4.

    Lookup values are matched case-insensitively against names, so both
    ?formula=glitter and ?formula=Glitter work. Repeat a param to OR within a
    facet (?color=teal&color=blue); different facets AND together.
    """

    formula = filters.BaseInFilter(method="filter_formula")
    color = filters.BaseInFilter(method="filter_color")
    tag = filters.BaseInFilter(method="filter_tag")
    brand = filters.CharFilter(method="filter_brand")
    in_collection = filters.BooleanFilter(field_name="in_collection")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Polish
        fields = ["formula", "color", "tag", "brand", "in_collection"]

    def filter_formula(self, queryset, name, value):
        return filter_by_names(queryset, "formulas", value)

    def filter_color(self, queryset, name, value):
        return filter_by_names(queryset, "colors", value)

    def filter_tag(self, queryset, name, value):
        return filter_by_names(queryset, "tags", value)

    def filter_brand(self, queryset, name, value):
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(brand_id=int(value))
        return queryset.filter(brand__name__iexact=value.replace("-", " ").strip())

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(brand__name__icontains=value)
        ).distinct()
