from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("datahub", "0006_record_observation"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="recordobservation",
            old_name="datahub_reco_record_o_9f4a8e_idx",
            new_name="datahub_rec_record__902f85_idx",
        ),
        migrations.RenameIndex(
            model_name="recordobservation",
            old_name="datahub_reco_source_d8f2a7_idx",
            new_name="datahub_rec_source__802aef_idx",
        ),
    ]
