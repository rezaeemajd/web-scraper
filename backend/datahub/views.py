from rest_framework import viewsets
from .models import EntityType,EntityField,Location,RawCapture,ExtractedRecord,DedupCandidate,ReviewTask,AuditEvent
from .serializers import EntityTypeSerializer,EntityFieldSerializer,LocationSerializer,RawCaptureSerializer,ExtractedRecordSerializer,DedupCandidateSerializer,ReviewTaskSerializer,AuditEventSerializer
class EntityTypeViewSet(viewsets.ModelViewSet): queryset=EntityType.objects.prefetch_related("fields"); serializer_class=EntityTypeSerializer; search_fields=["name","slug"]
class EntityFieldViewSet(viewsets.ModelViewSet): queryset=EntityField.objects.select_related("entity_type"); serializer_class=EntityFieldSerializer; filterset_fields=["entity_type","data_type","required"]
class LocationViewSet(viewsets.ModelViewSet): queryset=Location.objects.all(); serializer_class=LocationSerializer; search_fields=["country","province","city","district","address"]; filterset_fields=["country","province","city","district"]
class RawCaptureViewSet(viewsets.ReadOnlyModelViewSet): queryset=RawCapture.objects.all(); serializer_class=RawCaptureSerializer; search_fields=["url","body_sha256"]
class ExtractedRecordViewSet(viewsets.ModelViewSet): queryset=ExtractedRecord.objects.select_related("entity_type","location","raw_capture"); serializer_class=ExtractedRecordSerializer; search_fields=["source_domain","source_url","status","canonical_key"]; filterset_fields=["entity_type","status","source_domain"]; ordering_fields=["collected_at","quality_score","confidence"]
class DedupCandidateViewSet(viewsets.ModelViewSet): queryset=DedupCandidate.objects.select_related("record_a","record_b"); serializer_class=DedupCandidateSerializer; filterset_fields=["status"]
class ReviewTaskViewSet(viewsets.ModelViewSet): queryset=ReviewTask.objects.select_related("record","assigned_to"); serializer_class=ReviewTaskSerializer; filterset_fields=["status","assigned_to"]
class AuditEventViewSet(viewsets.ReadOnlyModelViewSet): queryset=AuditEvent.objects.select_related("actor"); serializer_class=AuditEventSerializer; filterset_fields=["action","entity","object_id"]
