from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EntityType,EntityField,Location,RawCapture,ExtractedRecord,DedupCandidate,ReviewTask,AuditEvent
from .serializers import EntityTypeSerializer,EntityFieldSerializer,LocationSerializer,RawCaptureSerializer,ExtractedRecordSerializer,DedupCandidateSerializer,ReviewTaskSerializer,AuditEventSerializer
from .review import transition_review_task\nfrom .dedup_review import resolve_dedup_candidate
class EntityTypeViewSet(viewsets.ModelViewSet): queryset=EntityType.objects.prefetch_related("fields"); serializer_class=EntityTypeSerializer; search_fields=["name","slug"]
class EntityFieldViewSet(viewsets.ModelViewSet): queryset=EntityField.objects.select_related("entity_type"); serializer_class=EntityFieldSerializer; filterset_fields=["entity_type","data_type","required"]
class LocationViewSet(viewsets.ModelViewSet): queryset=Location.objects.all(); serializer_class=LocationSerializer; search_fields=["country","province","city","district","address"]; filterset_fields=["country","province","city","district"]
class RawCaptureViewSet(viewsets.ReadOnlyModelViewSet): queryset=RawCapture.objects.all(); serializer_class=RawCaptureSerializer; search_fields=["url","body_sha256"]
class ExtractedRecordViewSet(viewsets.ModelViewSet): queryset=ExtractedRecord.objects.select_related("entity_type","location","raw_capture"); serializer_class=ExtractedRecordSerializer; search_fields=["source_domain","source_url","status","canonical_key"]; filterset_fields=["entity_type","status","source_domain"]; ordering_fields=["collected_at","quality_score","confidence"]
class DedupCandidateViewSet(viewsets.ModelViewSet):
    queryset=DedupCandidate.objects.select_related("record_a","record_b"); serializer_class=DedupCandidateSerializer; filterset_fields=["status"]
    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        try:
            candidate=resolve_dedup_candidate(candidate_id=pk,status=request.data.get("status"),winner_id=request.data.get("winner_id"),actor=request.user)
        except DedupCandidate.DoesNotExist:
            return Response({"detail":"dedup candidate not found"},status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail":str(exc)},status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(candidate).data)
class ReviewTaskViewSet(viewsets.ModelViewSet):
    queryset=ReviewTask.objects.select_related("record","assigned_to"); serializer_class=ReviewTaskSerializer; filterset_fields=["status","assigned_to"]
    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        new_status=request.data.get("status")
        notes=request.data.get("notes")
        try:
            task=transition_review_task(task_id=pk,status=new_status,actor=request.user,notes=notes)
        except ReviewTask.DoesNotExist:
            return Response({"detail":"review task not found"},status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail":str(exc)},status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(task).data)
class AuditEventViewSet(viewsets.ReadOnlyModelViewSet): queryset=AuditEvent.objects.select_related("actor"); serializer_class=AuditEventSerializer; filterset_fields=["action","entity","object_id"]
