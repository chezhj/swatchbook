from rest_framework.pagination import PageNumberPagination


class SwatchbookPagination(PageNumberPagination):
    """The swatch grid wants the whole collection in one go; everything else defaults.

    A personal collection is a few hundred rows at most, so an explicit page_size is
    cheaper than paginating the grid. The cap keeps the param from being abused.
    """

    page_size_query_param = "page_size"
    max_page_size = 500
