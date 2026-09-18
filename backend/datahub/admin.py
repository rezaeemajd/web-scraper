from django.contrib import admin
from .models import EntityType,Location,ExtractedRecord
admin.site.register([EntityType,Location,ExtractedRecord])
