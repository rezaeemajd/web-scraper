from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0004_record_normalized_payload_gin"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="extractedrecord",
            name="record_norm_payload_gin",
        ),
        migrations.AddIndex(
            model_name="extractedrecord",
            index=GinIndex(
                fields=["normalized_payload"],
                name="record_norm_payload_path_gin",
                opclasses=["jsonb_path_ops"],
            ),
        ),
    ]
