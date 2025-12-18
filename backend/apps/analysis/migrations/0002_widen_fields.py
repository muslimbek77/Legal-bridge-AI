from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisresult',
            name='model_used',
            field=models.CharField(blank=True, max_length=255, verbose_name='Ishlatilgan model'),
        ),
        migrations.AlterField(
            model_name='complianceissue',
            name='section_reference',
            field=models.CharField(blank=True, max_length=255, verbose_name="Bo'lim"),
        ),
        migrations.AlterField(
            model_name='complianceissue',
            name='clause_reference',
            field=models.CharField(blank=True, max_length=255, verbose_name='Band'),
        ),
        migrations.AlterField(
            model_name='complianceissue',
            name='law_article',
            field=models.CharField(blank=True, max_length=255, verbose_name='Qonun moddasi'),
        ),
    ]
