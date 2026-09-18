from rest_framework import viewsets
from .models import ExtractedRecord
from .serializers import ExtractedRecordSerializer
class ExtractedRecordViewSet(viewsets.ModelViewSet): queryset=ExtractedRecord.objects.select_related("entity_type","location"); serializer_class=ExtractedRecordSerializer; search_fields=["source_domain","source_url","status"]
