from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("scraping","0001_initial"),("datahub","0002_p1_core_data_engine")]
    operations=[
        migrations.AddField(model_name="scraper",name="entity_type",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="scrapers",to="datahub.entitytype")),
        migrations.AddField(model_name="scraper",name="extraction_config",field=models.JSONField(blank=True,default=dict)),
    ]
