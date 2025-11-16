# Generated manually for Acción 9: Constraints y validaciones
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_add_product_weight'),
    ]

    operations = [
        # Constraint: El precio debe ser mayor que 0
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='product_price_positive'
            ),
        ),
    ]
