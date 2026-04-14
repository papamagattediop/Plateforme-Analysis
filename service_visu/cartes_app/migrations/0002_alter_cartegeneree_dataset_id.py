from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cartes_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartegeneree',
            name='dataset_id',
            field=models.CharField(max_length=255),
        ),
    ]
