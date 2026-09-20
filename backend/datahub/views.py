from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import StaffWritePermission
from .dedup_review import resolve_dedup_candidate
from .models import (
    AuditEvent,
    DedupCandidate,
    EntityField,
    EntityType,
    ExtractedRecord,
    Location,
    RawCapture,
    RecordChange,
    RecordObservation,
    ReviewTask,
)
from .review import transition_review_task
from .serializers import (
    AuditEventSerializer,
    DedupCandidateSerializer,
    EntityFieldSerializer,
    EntityTypeSerializer,
    ExtractedRecordListSerializer,
    ExtractedRecordSerializer,
    LocationSerializer,
    RawCaptureListSerializer,
    RawCaptureSerializer,
    RecordChangeSerializer,
    RecordObservationSerializer,
    ReviewTaskSerializer,
)


class EntityTypeViewSet(viewsets.ModelViewSet):
    queryset = EntityType.objects.prefetch_related("fields")
    serializer_class = EntityTypeSerializer
    permission_classes = [StaffWritePermission]
    search_fields = ["name", "slug"]


class EntityFieldViewSet(viewsets.ModelViewSet):
    queryset = EntityField.objects.select_related("entity_type")
    serializer_class = EntityFieldSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["entity_type", "data_type", "required"]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [StaffWritePermission]
    search_fields = ["country", "province", "city", "district", "address"]
    filterset_fields = ["country", "province", "city", "district"]


class RawCaptureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RawCapture.objects.all()
    serializer_class = RawCaptureSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            return queryset.defer("body", "headers")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RawCaptureListSerializer
        return RawCaptureSerializer
    permission_classes = [StaffWritePermission]
    search_fields = ["url", "body_sha256"]


class ExtractedRecordViewSet(viewsets.ModelViewSet):
    queryset = ExtractedRecord.objects.select_related(
        "entity_type", "location", "raw_capture"
    )
    serializer_class = ExtractedRecordSerializer
    permission_classes = [StaffWritePermission]
    search_fields = ["source_domain", "source_url", "status", "canonical_key"]
    filterset_fields = ["entity_type", "status", "source_domain"]
    ordering_fields = ["collected_at", "quality_score", "confidence"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            return queryset.defer(
                "payload",
                "normalized_payload",
                "evidence",
                "validation_errors",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ExtractedRecordListSerializer
        return ExtractedRecordSerializer


class DedupCandidateViewSet(viewsets.ModelViewSet):
    queryset = DedupCandidate.objects.select_related("record_a", "record_b")
    serializer_class = DedupCandidateSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        try:
            candidate = resolve_dedup_candidate(
                candidate_id=pk,
                status=request.data.get("status"),
                winner_id=request.data.get("winner_id"),
                actor=request.user,
            )
        except DedupCandidate.DoesNotExist:
            return Response(
                {"detail": "dedup candidate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(self.get_serializer(candidate).data)


class ReviewTaskViewSet(viewsets.ModelViewSet):
    queryset = ReviewTask.objects.select_related("record", "assigned_to")
    serializer_class = ReviewTaskSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["status", "assigned_to"]

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        new_status = request.data.get("status")
        notes = request.data.get("notes")
        try:
            task = transition_review_task(
                task_id=pk,
                status=new_status,
                actor=request.user,
                notes=notes,
            )
        except ReviewTask.DoesNotExist:
            return Response(
                {"detail": "review task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(self.get_serializer(task).data)


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related("actor")
    serializer_class = AuditEventSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["action", "entity", "object_id"]


class RecordObservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecordObservation.objects.select_related("record", "raw_capture")
    serializer_class = RecordObservationSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["record", "source_domain"]
    ordering_fields = ["observed_at"]

class RecordChangeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecordChange.objects.select_related("record", "observation", "previous_observation")
    serializer_class = RecordChangeSerializer
    permission_classes = [StaffWritePermission]
    filterset_fields = ["record"]
    ordering_fields = ["detected_at"]
