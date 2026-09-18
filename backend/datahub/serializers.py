from rest_framework import serializers
from .models import ExtractedRecord
class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta: model=ExtractedRecord; fields="__all__"
