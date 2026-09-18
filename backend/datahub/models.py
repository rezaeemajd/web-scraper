from django.db import models
class EntityType(models.Model):
    name=models.CharField(max_length=100,unique=True); slug=models.SlugField(unique=True)
class Location(models.Model):
    country=models.CharField(max_length=100,default="ایران"); province=models.CharField(max_length=100,blank=True); city=models.CharField(max_length=100,blank=True); district=models.CharField(max_length=100,blank=True); address=models.TextField(blank=True)
class ExtractedRecord(models.Model):
    class Status(models.TextChoices): RAW="raw","Raw"; PARSED="parsed","Parsed"; REVIEW="needs_review","Needs Review"; APPROVED="approved","Approved"; REJECTED="rejected","Rejected"; ARCHIVED="archived","Archived"
    entity_type=models.ForeignKey(EntityType,on_delete=models.PROTECT,null=True,blank=True); location=models.ForeignKey(Location,on_delete=models.SET_NULL,null=True,blank=True); source_url=models.URLField(max_length=2000); source_domain=models.CharField(max_length=255,db_index=True); payload=models.JSONField(default=dict); status=models.CharField(max_length=20,choices=Status.choices,default=Status.RAW); confidence=models.DecimalField(max_digits=5,decimal_places=4,default=0); collected_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
