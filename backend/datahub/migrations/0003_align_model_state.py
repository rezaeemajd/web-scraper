from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0002_p1_core_data_engine"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="entitytype",
            options={"ordering": ["name"]},
        ),
        migrations.RenameIndex(
            model_name="extractedrecord",
            old_name="datahub_ext_entity__7d7c1c_idx",
            new_name="datahub_ext_entity__21b5a2_idx",
        ),
        migrations.RenameIndex(
            model_name="extractedrecord",
            old_name="datahub_ext_source_d1f6c0_idx",
            new_name="datahub_ext_source__2b96f7_idx",
        ),
        migrations.AlterField(
            model_name="location",
            name="city",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="location",
            name="country",
            field=models.CharField(blank=True, db_index=True, default="ایران", max_length=100),
        ),
        migrations.AlterField(
            model_name="location",
            name="district",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="location",
            name="province",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
    ]
