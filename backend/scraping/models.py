from django.db import models
from django.db.models import Q
from sources.models import Source
class Scraper(models.Model):
    name=models.CharField(max_length=200); source=models.ForeignKey(Source,on_delete=models.PROTECT,related_name="scrapers"); method=models.CharField(max_length=40,default="static_html"); start_url=models.URLField(); active=models.BooleanField(default=True); parser_version=models.CharField(max_length=40,default="1.0.0"); entity_type=models.ForeignKey("datahub.EntityType",on_delete=models.PROTECT,null=True,blank=True,related_name="scrapers"); extraction_config=models.JSONField(default=dict,blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
class ScraperRun(models.Model):
    class Status(models.TextChoices): QUEUED="queued","Queued"; RUNNING="running","Running"; SUCCESS="success","Success"; BLOCKED="blocked","Blocked"; FAILED="failed","Failed"
    scraper=models.ForeignKey(Scraper,on_delete=models.CASCADE,related_name="runs"); status=models.CharField(max_length=20,choices=Status.choices,default=Status.QUEUED); started_at=models.DateTimeField(null=True,blank=True); finished_at=models.DateTimeField(null=True,blank=True); pages_fetched=models.PositiveIntegerField(default=0); records_extracted=models.PositiveIntegerField(default=0); error_message=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["scraper"],condition=Q(status__in=["queued","running"]),name="uniq_scraper_active_run")]
