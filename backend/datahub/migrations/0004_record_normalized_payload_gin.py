from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0003_align_model_state"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="extractedrecord",
            index=GinIndex(
                fields=["normalized_payload"],
                name="record_norm_payload_gin",
            ),
        ),
    ]
