from pathlib import Path

from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import ExportJob
from .serializers import ExportJobSerializer
from .tasks import run_export


class ExportJobViewSet(viewsets.ModelViewSet):
    queryset = ExportJob.objects.order_by("-created_at")
    serializer_class = ExportJobSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "head", "options"]

    def perform_create(self, serializer):
        job = serializer.save()
        from django.db import transaction
        transaction.on_commit(lambda: run_export.delay(job.pk))

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        job = self.get_object()
        if job.status != ExportJob.Status.SUCCESS or not job.file_path:
            return Response(
                {"detail": "export is not ready"},
                status=status.HTTP_409_CONFLICT,
            )
        path = Path(job.file_path)
        if not path.is_file():
            return Response(
                {"detail": "export file is missing"},
                status=status.HTTP_410_GONE,
            )
        return FileResponse(
            path.open("rb"),
            as_attachment=True,
            filename=path.name,
        )
