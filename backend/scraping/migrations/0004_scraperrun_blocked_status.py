from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scraping", "0003_active_run_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scraperrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("queued", "Queued"),
                    ("running", "Running"),
                    ("success", "Success"),
                    ("blocked", "Blocked"),
                    ("failed", "Failed"),
                ],
                default="queued",
                max_length=20,
            ),
        ),
    ]
}
