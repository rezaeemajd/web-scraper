from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import ExportJob
from .views import ExportJobViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register("jobs", ExportJobViewSet, basename="export-job")

@api_view(["GET"])
def export_status(request):
    return Response({"service": "exports", "formats": [x.value for x in ExportJob.Format]})

urlpatterns = [path("status/", export_status), path("", include(router.urls))]
