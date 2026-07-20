from django.urls import reverse
from rest_framework import serializers

from .models import LogEntry, LogEntryPolish, LogPhoto


class LogPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogPhoto
        fields = ["id", "image"]


class LogEntryPolishSerializer(serializers.ModelSerializer):
    polish_name = serializers.CharField(source="polish.name", read_only=True)
    brand_name = serializers.CharField(source="polish.brand.name", read_only=True)
    photo_url = serializers.CharField(source="polish.photo_url", read_only=True)
    finish_classes = serializers.ListField(
        source="polish.finish_classes", child=serializers.CharField(), read_only=True
    )

    class Meta:
        model = LogEntryPolish
        fields = [
            "id",
            "polish",
            "polish_name",
            "brand_name",
            "photo_url",
            "finish_classes",
            "role",
        ]


class LogEntrySerializer(serializers.ModelSerializer):
    entry_polishes = LogEntryPolishSerializer(many=True, required=False)
    photos = LogPhotoSerializer(many=True, read_only=True)
    # `title` is the user's own (writable, may be blank); `display_title` is what a
    # list row shows — the title, else the polishes worn.
    display_title = serializers.CharField(read_only=True)
    photo_url = serializers.CharField(read_only=True)
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            "id",
            "date_worn",
            "title",
            "display_title",
            "notes",
            "entry_polishes",
            "photos",
            "photo_url",
            "detail_url",
        ]

    def get_detail_url(self, obj):
        return reverse("log_detail", args=[obj.pk])

    def create(self, validated_data):
        rows = validated_data.pop("entry_polishes", [])
        entry = LogEntry.objects.create(**validated_data)
        self._sync_polishes(entry, rows)
        return entry

    def update(self, instance, validated_data):
        rows = validated_data.pop("entry_polishes", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if rows is not None:
            instance.entry_polishes.all().delete()
            self._sync_polishes(instance, rows)
        return instance

    def _sync_polishes(self, entry, rows):
        for row in rows:
            LogEntryPolish.objects.create(
                log_entry=entry,
                polish=row["polish"],
                role=row.get("role", "base"),
            )
