from django.db import models
class ExportJob(models.Model):
    class Format(models.TextChoices): CSV="csv","CSV"; XLSX="xlsx","XLSX"; JSON="json","JSON"; JSONL="jsonl","JSONL"; TXT="txt","TXT"; DOCX="docx","DOCX"; PDF="pdf","PDF"
    class Status(models.TextChoices): QUEUED="queued","Queued"; RUNNING="running","Running"; SUCCESS="success","Success"; FAILED="failed","Failed"
    format=models.CharField(max_length=10,choices=Format.choices); status=models.CharField(max_length=20,choices=Status.choices,default=Status.QUEUED); filters=models.JSONField(default=dict); file_path=models.CharField(max_length=500,blank=True); error_message=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True)
