from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("sources","0001_initial")]
    operations=[
        migrations.AddField(model_name="source",name="user_agent",field=models.CharField(default="CDI/1.0 (+https://cofinets.com)",max_length=255)),
        migrations.AddField(model_name="source",name="max_response_bytes",field=models.PositiveIntegerField(default=5242880)),
    ]
