from rest_framework import viewsets
from .models import Source
from .serializers import SourceSerializer
class SourceViewSet(viewsets.ModelViewSet): queryset=Source.objects.all(); serializer_class=SourceSerializer; search_fields=["name","domain"]; ordering_fields=["name","priority","created_at"]
