from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0003_expand_section_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='party_a',
            field=models.CharField(blank=True, max_length=1000, verbose_name='1-tomon'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='party_b',
            field=models.CharField(blank=True, max_length=1000, verbose_name='2-tomon'),
        ),
    ]
