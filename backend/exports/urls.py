from django.urls import path
from .models import ExportJob
from rest_framework.decorators import api_view
from rest_framework.response import Response
@api_view(["GET"])
def export_status(request): return Response({"service":"exports","formats":[x.value for x in ExportJob.Format]})
urlpatterns=[path("status/",export_status)]
