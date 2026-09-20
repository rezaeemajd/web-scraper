from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0008_identity_blocking_metadata"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecordChange",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_fields", models.JSONField(default=list)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                ("observation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="change", to="datahub.recordobservation")),
                ("previous_observation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="changes_from", to="datahub.recordobservation")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="changes", to="datahub.extractedrecord")),
            ],
            options={"ordering": ["-detected_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="recordchange",
            constraint=models.UniqueConstraint(fields=("record", "observation"), name="uniq_record_change_observation"),
        ),
    ]
