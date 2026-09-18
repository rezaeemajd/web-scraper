from django.db import migrations, models
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[migrations.CreateModel(name="ExportJob",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("format",models.CharField(choices=[("csv","CSV"),("xlsx","XLSX"),("json","JSON"),("jsonl","JSONL"),("docx","DOCX"),("pdf","PDF")],max_length=10)),("status",models.CharField(choices=[("queued","Queued"),("running","Running"),("success","Success"),("failed","Failed")],default="queued",max_length=20)),("filters",models.JSONField(default=dict)),("file_path",models.CharField(blank=True,max_length=500)),("error_message",models.TextField(blank=True)),("created_at",models.DateTimeField(auto_now_add=True))])]
