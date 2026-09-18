from rest_framework import serializers
from .models import Scraper,ScraperRun
class ScraperSerializer(serializers.ModelSerializer):
    class Meta: model=Scraper; fields="__all__"
class ScraperRunSerializer(serializers.ModelSerializer):
    class Meta: model=ScraperRun; fields="__all__"
