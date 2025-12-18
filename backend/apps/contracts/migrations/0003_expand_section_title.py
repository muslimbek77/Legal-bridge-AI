from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0002_expand_contract_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractsection',
            name='title',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Sarlavha'),
        ),
    ]
