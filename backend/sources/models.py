from django.db import models
class Source(models.Model):
    class Status(models.TextChoices): ACTIVE="active","Active"; PAUSED="paused","Paused"; DISABLED="disabled","Disabled"
    name=models.CharField(max_length=200); domain=models.CharField(max_length=255,db_index=True); base_url=models.URLField(); status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE); priority=models.PositiveSmallIntegerField(default=50); rate_limit_per_minute=models.PositiveIntegerField(default=30); respect_robots=models.BooleanField(default=True); allowed=models.BooleanField(default=True); notes=models.TextField(blank=True); user_agent=models.CharField(max_length=255,default="CDI/1.0 (+https://cofinets.com)"); max_response_bytes=models.PositiveIntegerField(default=5242880); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["-priority","name"]
    def __str__(self): return self.name
