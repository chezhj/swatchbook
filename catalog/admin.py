from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Collection, Color, Formula, Polish, PolishPhoto, Tag


class PolishPhotoInline(admin.TabularInline):
    model = PolishPhoto
    extra = 1


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "code_prefix", "polish_count", "website"]
    search_fields = ["name"]
    inlines = [CollectionInline]

    @admin.display(description="Polishes")
    def polish_count(self, obj):
        return obj.polishes.count()


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "brand", "year"]
    list_filter = ["brand", "year"]
    search_fields = ["name", "brand__name"]


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ["name", "css_class"]


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ["name", "swatch"]

    @admin.display(description="Swatch")
    def swatch(self, obj):
        if not obj.hex_color:
            return "—"
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            'border-radius:4px;background:{};"></span>',
            obj.hex_color,
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "polish_count"]
    search_fields = ["name"]

    @admin.display(description="Polishes")
    def polish_count(self, obj):
        return obj.polishes.count()


@admin.register(Polish)
class PolishAdmin(admin.ModelAdmin):
    list_display = ["catalog_code", "swatch", "name", "brand", "collection", "in_collection"]
    list_display_links = ["catalog_code", "name"]
    list_filter = ["in_collection", "brand", "formulas", "colors", "tags"]
    search_fields = ["name", "catalog_code", "brand__name", "description"]
    filter_horizontal = ["formulas", "colors", "tags"]
    inlines = [PolishPhotoInline]
    readonly_fields = ["created_at"]
    fieldsets = [
        (None, {"fields": ["name", "brand", "collection", "catalog_code", "in_collection"]}),
        ("Appearance", {"fields": ["hex_color", "formulas", "colors"]}),
        ("Details", {"fields": ["description", "tags", "webshop_link", "created_at"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("brand", "collection")

    @admin.display(description="")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:24px;height:24px;'
            'border-radius:6px;background:{};"></span>',
            obj.hex_color,
        )
