from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0005_record_normalized_payload_path_gin"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecordObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_url", models.URLField(max_length=2000)),
                ("source_domain", models.CharField(db_index=True, max_length=255)),
                ("payload", models.JSONField(default=dict)),
                ("normalized_payload", models.JSONField(default=dict)),
                ("evidence", models.JSONField(blank=True, default=list)),
                ("fingerprint", models.CharField(blank=True, db_index=True, max_length=64)),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                ("raw_capture", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="observations", to="datahub.rawcapture")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="observations", to="datahub.extractedrecord")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["record", "observed_at"], name="datahub_reco_record_o_9f4a8e_idx"),
                    models.Index(fields=["source_domain", "observed_at"], name="datahub_reco_source_d8f2a7_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="recordobservation",
            constraint=models.UniqueConstraint(
                fields=("record", "raw_capture"),
                condition=Q(raw_capture__isnull=False),
                name="uniq_record_observation_capture",
            ),
        ),
    ]
