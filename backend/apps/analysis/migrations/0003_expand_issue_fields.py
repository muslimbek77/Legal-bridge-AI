from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0002_widen_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complianceissue',
            name='title',
            field=models.CharField(max_length=1000, verbose_name='Sarlavha'),
        ),
        migrations.AlterField(
            model_name='complianceissue',
            name='law_name',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Qonun nomi'),
        ),
    ]
