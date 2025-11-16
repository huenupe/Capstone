# Generated manually for Acción 9: Constraints y validaciones
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_rename_index_for_consistency'),
    ]

    operations = [
        # Constraints para Order
        # El monto total debe ser mayor que 0
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(
                condition=models.Q(total_amount__gt=0),
                name='order_total_amount_positive'
            ),
        ),
        # El costo de envío no puede ser negativo
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(
                condition=models.Q(shipping_cost__gte=0),
                name='order_shipping_cost_non_negative'
            ),
        ),
        
        # Constraints para OrderItem
        # La cantidad debe ser mayor que 0
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='order_item_quantity_positive'
            ),
        ),
        # El precio unitario debe ser mayor que 0
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name='order_item_unit_price_positive'
            ),
        ),
        # El precio total debe ser mayor que 0
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(
                condition=models.Q(total_price__gt=0),
                name='order_item_total_price_positive'
            ),
        ),
    ]
