from rest_framework import serializers
from .models import EntityType,EntityField,Location,RawCapture,ExtractedRecord,DedupCandidate,ReviewTask,AuditEvent
class EntityFieldSerializer(serializers.ModelSerializer):
    class Meta: model=EntityField; fields="__all__"
class EntityTypeSerializer(serializers.ModelSerializer):
    fields=EntityFieldSerializer(many=True,read_only=True)
    class Meta: model=EntityType; fields="__all__"
class LocationSerializer(serializers.ModelSerializer):
    class Meta: model=Location; fields="__all__"
class RawCaptureSerializer(serializers.ModelSerializer):
    class Meta: model=RawCapture; fields="__all__"
class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta: model=ExtractedRecord; fields="__all__"; read_only_fields=["normalized_payload","fingerprint","quality_score","validation_errors","status","collected_at","updated_at"]

    def validate(self, attrs):
        if "status" in self.initial_data:
            raise serializers.ValidationError({"status": "status is managed by the workflow"})
        return super().validate(attrs)
class DedupCandidateSerializer(serializers.ModelSerializer):
    class Meta: model=DedupCandidate; fields="__all__"; read_only_fields=["status","created_at"]

    def validate(self, attrs):
        if "status" in self.initial_data:
            raise serializers.ValidationError({"status": "status is managed by the workflow"})
        return super().validate(attrs)
class ReviewTaskSerializer(serializers.ModelSerializer):
    class Meta: model=ReviewTask; fields="__all__"; read_only_fields=["status","created_at","updated_at"]

    def validate(self, attrs):
        if "status" in self.initial_data:
            raise serializers.ValidationError({"status": "status is managed by the workflow"})
        return super().validate(attrs)
class AuditEventSerializer(serializers.ModelSerializer):
    class Meta: model=AuditEvent; fields="__all__"
