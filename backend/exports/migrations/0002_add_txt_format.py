from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("exports", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="exportjob",
            name="format",
            field=models.CharField(
                choices=[
                    ("csv", "CSV"),
                    ("xlsx", "XLSX"),
                    ("json", "JSON"),
                    ("jsonl", "JSONL"),
                    ("txt", "TXT"),
                    ("docx", "DOCX"),
                    ("pdf", "PDF"),
                ],
                max_length=10,
            ),
        ),
    ]
