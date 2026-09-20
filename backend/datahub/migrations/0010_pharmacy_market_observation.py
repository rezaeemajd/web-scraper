from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0009_record_change"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pharmacy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("source_url", models.URLField(max_length=2000)),
                ("source_domain", models.CharField(db_index=True, max_length=255)),
                ("canonical_key", models.CharField(blank=True, db_index=True, max_length=255)),
                ("pharmacy_type", models.CharField(blank=True, max_length=120)),
                ("service_hours", models.CharField(blank=True, max_length=255)),
                ("public_phone", models.CharField(blank=True, max_length=64)),
                ("website", models.URLField(blank=True, max_length=2000)),
                ("evidence", models.JSONField(blank=True, default=list)),
                ("active", models.BooleanField(default=True)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("location", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pharmacies", to="datahub.location")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["source_domain", "name"], name="datahub_phar_source__4b7b5f_idx"),
                    models.Index(fields=["location", "active"], name="datahub_phar_locatio_9e53f1_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("source_domain", "source_url"), name="uniq_pharmacy_source_url"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MarketObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_url", models.URLField(max_length=2000)),
                ("source_domain", models.CharField(db_index=True, max_length=255)),
                ("availability", models.CharField(choices=[("listed", "Listed"), ("available", "Available"), ("unavailable", "Unavailable"), ("not_stated", "Not stated"), ("unknown", "Unknown")], default="unknown", max_length=20)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("price_currency", models.CharField(blank=True, max_length=12)),
                ("price_text", models.CharField(blank=True, max_length=255)),
                ("quantity", models.PositiveIntegerField(blank=True, null=True)),
                ("evidence", models.JSONField(blank=True, default=list)),
                ("observed_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pharmacy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_observations", to="datahub.pharmacy")),
                ("raw_capture", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="market_observations", to="datahub.rawcapture")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_observations", to="datahub.extractedrecord")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["record", "-observed_at"], name="datahub_mark_record__8e8e0d_idx"),
                    models.Index(fields=["pharmacy", "-observed_at"], name="datahub_mark_pharmac_5b8d6d_idx"),
                    models.Index(fields=["source_domain", "-observed_at"], name="datahub_mark_source__2e2f39_idx"),
                    models.Index(fields=["availability", "-observed_at"], name="datahub_mark_availab_0cda48_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("pharmacy", "record", "source_url", "observed_at"), name="uniq_market_observation_point"),
                ],
            },
        ),
    ]
