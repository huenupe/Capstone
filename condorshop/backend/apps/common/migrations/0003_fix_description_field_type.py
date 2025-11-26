# Generated manually to fix description field type (TextField -> CharField)
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_add_hero_carousel_slide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='herocarouselslide',
            name='description',
            field=models.CharField(blank=True, db_column='description', help_text='Descripción breve del slide (opcional)', max_length=500, null=True, verbose_name='Descripción'),
        ),
    ]

