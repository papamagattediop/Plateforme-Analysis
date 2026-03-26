from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard_app', '0002_alter_dashboard_options_alter_widget_config_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dashboard',
            name='dataset_id',
            field=models.CharField(max_length=255),
        ),
    ]
