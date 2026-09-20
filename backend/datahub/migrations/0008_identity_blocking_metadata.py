from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0007_rename_record_observation_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="entityfield",
            name="is_identifier",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="entityfield",
            name="is_blocking",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="extractedrecord",
            constraint=models.UniqueConstraint(
                fields=("entity_type", "canonical_key"),
                condition=~Q(canonical_key=""),
                name="uniq_entity_record_canonical_key",
            ),
        ),
    ]
