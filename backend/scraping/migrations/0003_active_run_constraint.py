from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("scraping", "0002_entity_extraction"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="scraperrun",
            constraint=models.UniqueConstraint(
                fields=("scraper",),
                condition=Q(status__in=("queued", "running")),
                name="uniq_scraper_active_run",
            ),
        ),
    ]
}
