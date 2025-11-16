# Generated manually for Acción 7: Agregar weight a Product
from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_add_inventory_control'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.DecimalField(
                db_column='weight',
                decimal_places=2,
                default=Decimal('0'),
                help_text='Peso del producto en kilogramos',
                max_digits=10,
                verbose_name='Peso (kg)'
            ),
        ),
    ]

