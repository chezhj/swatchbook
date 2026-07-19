from django.urls import reverse
from rest_framework import serializers

from .models import Brand, Collection, Color, Formula, Polish, PolishPhoto, Tag


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "website"]


class CollectionSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "brand", "brand_name", "name", "year"]


class FormulaSerializer(serializers.ModelSerializer):
    css_class = serializers.CharField(read_only=True)

    class Meta:
        model = Formula
        fields = ["id", "name", "css_class"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", "hex_color"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PolishPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolishPhoto
        fields = ["id", "image", "is_primary"]


class PolishSerializer(serializers.ModelSerializer):
    """Everything a grid cell or detail view needs, in one round trip."""

    brand_name = serializers.CharField(source="brand.name", read_only=True)
    collection_name = serializers.CharField(source="collection.name", read_only=True, default=None)
    collection_year = serializers.IntegerField(
        source="collection.year", read_only=True, default=None
    )
    formula_names = serializers.SlugRelatedField(
        source="formulas", slug_field="name", many=True, read_only=True
    )
    color_names = serializers.SlugRelatedField(
        source="colors", slug_field="name", many=True, read_only=True
    )
    tag_names = serializers.SlugRelatedField(
        source="tags", slug_field="name", many=True, read_only=True
    )
    finish_classes = serializers.ListField(child=serializers.CharField(), read_only=True)
    photos = PolishPhotoSerializer(many=True, read_only=True)
    # Only present when the queryset was annotated (i.e. always, via get_queryset).
    last_used = serializers.DateField(read_only=True, required=False)
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Polish
        fields = [
            "id",
            "catalog_code",
            "name",
            "brand",
            "brand_name",
            "collection",
            "collection_name",
            "collection_year",
            "description",
            "webshop_link",
            "hex_color",
            "in_collection",
            "formulas",
            "formula_names",
            "colors",
            "color_names",
            "tags",
            "tag_names",
            "finish_classes",
            "photos",
            "last_used",
            "detail_url",
            "created_at",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {
            # Auto-generated when blank, so never require it on write.
            "catalog_code": {"required": False},
        }

    def get_detail_url(self, obj):
        # Note the underscore: the DRF router already owns the name "polish-detail".
        return reverse("polish_detail", args=[obj.pk])
