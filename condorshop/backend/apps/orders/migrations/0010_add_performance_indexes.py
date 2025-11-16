# Generated manually for Acción 8: Índices de performance
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_refactor_shipping_rules'),
    ]

    operations = [
        # Índice compuesto para optimizar queries que filtran por estado y ordenan por fecha
        # Útil para: Order.objects.filter(status=status).order_by('-created_at')
        # Nota: MySQL puede usar este índice para ordenamiento descendente aunque se defina ascendente
        # Nota: Nombre usa "orders" (plural) para mantener consistencia con otros índices
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['status', 'created_at'],
                name='idx_orders_status_created'
            ),
        ),
    ]
