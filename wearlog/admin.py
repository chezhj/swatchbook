from django.contrib import admin

from .models import LogEntry, LogEntryPolish, LogPhoto


class LogEntryPolishInline(admin.TabularInline):
    model = LogEntryPolish
    extra = 1
    autocomplete_fields = ["polish"]


class LogPhotoInline(admin.TabularInline):
    model = LogPhoto
    extra = 1


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["date_worn", "title", "photo_count"]
    list_filter = ["date_worn"]
    search_fields = ["notes", "polishes__name"]
    date_hierarchy = "date_worn"
    inlines = [LogEntryPolishInline, LogPhotoInline]

    def get_queryset(self, request):
        return super().get_queryset(request).with_related()

    @admin.display(description="Photos")
    def photo_count(self, obj):
        return obj.photos.count()
