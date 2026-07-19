"""DRF router mounted at /api/ — see spec section 4."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from catalog.api import (
    BrandViewSet,
    CollectionViewSet,
    ColorViewSet,
    FormulaViewSet,
    PolishViewSet,
    TagViewSet,
)
from wearlog.api import LogEntryViewSet

router = DefaultRouter()
router.register("brands", BrandViewSet, basename="brand")
router.register("collections", CollectionViewSet, basename="collection")
router.register("formulas", FormulaViewSet, basename="formula")
router.register("colors", ColorViewSet, basename="color")
router.register("tags", TagViewSet, basename="tag")
router.register("polishes", PolishViewSet, basename="polish")
router.register("log-entries", LogEntryViewSet, basename="logentry")

urlpatterns = [
    path("auth/", include("rest_framework.urls")),
    path("", include(router.urls)),
]
