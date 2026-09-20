from rest_framework import serializers

from .models import ExportJob


class ExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = [
            "id", "format", "status", "filters", "file_path",
            "error_message", "created_at",
        ]
        read_only_fields = ["id", "status", "file_path", "error_message", "created_at"]

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("filters must be an object")
        allowed = {
            "entity_type_id", "location_id", "source_domain", "status",
            "quality_min", "created_after", "created_before",
        }
        unknown = set(value) - allowed
        if unknown:
            raise serializers.ValidationError(
                f"unsupported filter(s): {', '.join(sorted(unknown))}"
            )
        return value
