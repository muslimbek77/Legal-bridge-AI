from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='title',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Shartnoma nomi'),
        ),
    ]
