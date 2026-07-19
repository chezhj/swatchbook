from rest_framework import serializers

from .models import LogEntry, LogEntryPolish, LogPhoto


class LogPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogPhoto
        fields = ["id", "image"]


class LogEntryPolishSerializer(serializers.ModelSerializer):
    polish_name = serializers.CharField(source="polish.name", read_only=True)
    brand_name = serializers.CharField(source="polish.brand.name", read_only=True)
    hex_color = serializers.CharField(source="polish.hex_color", read_only=True)
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
            "hex_color",
            "finish_classes",
            "role",
        ]


class LogEntrySerializer(serializers.ModelSerializer):
    entry_polishes = LogEntryPolishSerializer(many=True, required=False)
    photos = LogPhotoSerializer(many=True, read_only=True)
    title = serializers.CharField(read_only=True)

    class Meta:
        model = LogEntry
        fields = ["id", "date_worn", "notes", "title", "entry_polishes", "photos"]

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
