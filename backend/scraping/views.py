from rest_framework import viewsets

from core.permissions import StaffWritePermission
from .models import Scraper, ScraperRun
from .serializers import ScraperSerializer, ScraperRunSerializer


class ScraperViewSet(viewsets.ModelViewSet):
    queryset = Scraper.objects.select_related("source")
    serializer_class = ScraperSerializer
    permission_classes = [StaffWritePermission]


class ScraperRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScraperRun.objects.select_related("scraper")
    serializer_class = ScraperRunSerializer
    permission_classes = [StaffWritePermission]
