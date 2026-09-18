from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Q
class EntityType(models.Model):
    name=models.CharField(max_length=100,unique=True); slug=models.SlugField(unique=True); description=models.TextField(blank=True); active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["name"]
class EntityField(models.Model):
    class DataType(models.TextChoices): TEXT="text","Text"; INTEGER="integer","Integer"; DECIMAL="decimal","Decimal"; BOOLEAN="boolean","Boolean"; DATE="date","Date"; URL="url","URL"; JSON="json","JSON"
    entity_type=models.ForeignKey(EntityType,on_delete=models.CASCADE,related_name="fields"); name=models.CharField(max_length=100); slug=models.SlugField(max_length=100); data_type=models.CharField(max_length=20,choices=DataType.choices,default=DataType.TEXT); required=models.BooleanField(default=False); searchable=models.BooleanField(default=True); normalizer=models.CharField(max_length=100,blank=True); validators_config=models.JSONField(default=dict,blank=True); position=models.PositiveIntegerField(default=0)
    class Meta: ordering=["position","id"]; constraints=[models.UniqueConstraint(fields=["entity_type","slug"],name="uniq_entity_field_slug")]
class Location(models.Model):
    parent=models.ForeignKey("self",on_delete=models.PROTECT,null=True,blank=True,related_name="children"); country=models.CharField(max_length=100,default="ایران",db_index=True,blank=True); province=models.CharField(max_length=100,blank=True,db_index=True); city=models.CharField(max_length=100,blank=True,db_index=True); district=models.CharField(max_length=100,blank=True,db_index=True); address=models.TextField(blank=True); normalized_address=models.TextField(blank=True); latitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True); longitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True,null=True); updated_at=models.DateTimeField(auto_now=True,null=True)
class RawCapture(models.Model):
    class Status(models.TextChoices): SUCCESS="success","Success"; BLOCKED="blocked","Blocked"; ERROR="error","Error"
    url=models.URLField(max_length=2000); status_code=models.PositiveSmallIntegerField(null=True,blank=True); content_type=models.CharField(max_length=255,blank=True); body=models.TextField(blank=True); headers=models.JSONField(default=dict,blank=True); body_sha256=models.CharField(max_length=64,db_index=True,blank=True); status=models.CharField(max_length=20,choices=Status.choices,default="success"); error_message=models.TextField(blank=True); fetched_at=models.DateTimeField(auto_now_add=True)
class ExtractedRecord(models.Model):
    class Status(models.TextChoices): RAW="raw","Raw"; PARSED="parsed","Parsed"; REVIEW="needs_review","Needs Review"; APPROVED="approved","Approved"; REJECTED="rejected","Rejected"; ARCHIVED="archived","Archived"
    entity_type=models.ForeignKey(EntityType,on_delete=models.PROTECT,null=True,blank=True); location=models.ForeignKey(Location,on_delete=models.SET_NULL,null=True,blank=True); raw_capture=models.ForeignKey(RawCapture,on_delete=models.SET_NULL,null=True,blank=True,related_name="records"); source_url=models.URLField(max_length=2000); source_domain=models.CharField(max_length=255,db_index=True); payload=models.JSONField(default=dict); normalized_payload=models.JSONField(default=dict); evidence=models.JSONField(default=list,blank=True); status=models.CharField(max_length=20,choices=Status.choices,default="raw"); confidence=models.DecimalField(max_digits=5,decimal_places=4,default=0); quality_score=models.DecimalField(max_digits=5,decimal_places=4,default=0); canonical_key=models.CharField(max_length=255,db_index=True,blank=True); fingerprint=models.CharField(max_length=64,db_index=True,blank=True); validation_errors=models.JSONField(default=list,blank=True); collected_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        indexes=[
            models.Index(fields=["entity_type","status"]),
            models.Index(fields=["source_domain","collected_at"]),
            GinIndex(fields=["normalized_payload"], name="record_norm_payload_gin"),
        ]
        constraints=[models.UniqueConstraint(fields=["entity_type","fingerprint"],condition=~Q(fingerprint=""),name="uniq_entity_record_fingerprint")]
class DedupCandidate(models.Model):
    class Status(models.TextChoices): OPEN="open","Open"; MERGED="merged","Merged"; REJECTED="rejected","Rejected"
    record_a=models.ForeignKey(ExtractedRecord,on_delete=models.CASCADE,related_name="dedup_left"); record_b=models.ForeignKey(ExtractedRecord,on_delete=models.CASCADE,related_name="dedup_right"); similarity=models.DecimalField(max_digits=5,decimal_places=4); matched_fields=models.JSONField(default=list,blank=True); status=models.CharField(max_length=20,choices=Status.choices,default="open"); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["record_a","record_b"],name="uniq_dedup_pair")]
class ReviewTask(models.Model):
    class Status(models.TextChoices): OPEN="open","Open"; APPROVED="approved","Approved"; REJECTED="rejected","Rejected"; SKIPPED="skipped","Skipped"
    record=models.ForeignKey(ExtractedRecord,on_delete=models.CASCADE,related_name="review_tasks"); status=models.CharField(max_length=20,choices=Status.choices,default="open"); reason=models.CharField(max_length=255,blank=True); assigned_to=models.ForeignKey("auth.User",on_delete=models.SET_NULL,null=True,blank=True,related_name="cdi_review_tasks"); notes=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
class AuditEvent(models.Model):
    actor=models.ForeignKey("auth.User",on_delete=models.SET_NULL,null=True,blank=True); action=models.CharField(max_length=100); entity=models.CharField(max_length=100); object_id=models.CharField(max_length=100); before=models.JSONField(default=dict,blank=True); after=models.JSONField(default=dict,blank=True); metadata=models.JSONField(default=dict,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
