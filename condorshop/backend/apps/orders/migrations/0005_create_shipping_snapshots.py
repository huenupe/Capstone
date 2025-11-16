# Generated manually for refactoring - Acción 1

from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_orders(apps, schema_editor):
    """
    Crea snapshots para órdenes existentes.
    
    IMPORTANTE: Esta función migra datos ANTES de eliminar los campos
    de Order. Si no hay órdenes existentes, no hace nada.
    """
    Order = apps.get_model('orders', 'Order')
    OrderShippingSnapshot = apps.get_model('orders', 'OrderShippingSnapshot')
    User = apps.get_model('users', 'User')
    
    # Obtener todas las órdenes con user relacionado
    orders = Order.objects.select_related('user').all()
    
    if not orders.exists():
        # No hay órdenes, no hay nada que migrar
        return
    
    for order in orders:
        # Obtener datos del cliente
        name = None
        email = None
        phone = None
        
        # Intentar obtener desde campos directos de Order
        if hasattr(order, 'customer_name'):
            name = order.customer_name
        if hasattr(order, 'customer_email'):
            email = order.customer_email
        if hasattr(order, 'customer_phone'):
            phone = order.customer_phone
        
        # Fallback: obtener desde User si existe y campos están vacíos
        if order.user:
            if not name:
                # Intentar get_full_name() o usar username/email
                if hasattr(order.user, 'get_full_name'):
                    name = order.user.get_full_name()
                if not name:
                    name = order.user.username or order.user.email
            if not email:
                email = order.user.email
            if not phone and hasattr(order.user, 'phone'):
                phone = order.user.phone or ''
        
        # Valores por defecto seguros
        name = name or 'Cliente sin nombre'
        email = email or 'sin-email@ejemplo.com'
        phone = phone or ''
        
        # Obtener datos de envío (con hasattr para seguridad)
        shipping_street = getattr(order, 'shipping_street', '') or ''
        shipping_city = getattr(order, 'shipping_city', '') or ''
        shipping_region = getattr(order, 'shipping_region', '') or ''
        shipping_postal_code = getattr(order, 'shipping_postal_code', '') or ''
        
        # shipping_country default
        shipping_country = 'Chile'
        
        # Intentar encontrar Address relacionada si existe
        original_address = None
        if order.user:
            try:
                # Buscar Address que coincida con datos de shipping
                Address = apps.get_model('users', 'Address')
                matching_address = Address.objects.filter(
                    user=order.user,
                    street=shipping_street,
                    city=shipping_city,
                    region=shipping_region
                ).first()
                if matching_address:
                    original_address = matching_address
            except Exception:
                # Si no existe modelo Address o falla, continuar sin original_address
                pass
        
        # Crear snapshot
        snapshot = OrderShippingSnapshot.objects.create(
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            shipping_street=shipping_street,
            shipping_city=shipping_city,
            shipping_region=shipping_region,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            original_user=order.user,
            original_address=original_address
        )
        
        # Vincular snapshot a Order
        order.shipping_snapshot = snapshot
        order.save(update_fields=['shipping_snapshot'])


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0004_alter_payment_amount'),
        ('users', '0001_initial'),
    ]

    operations = [
        # 1. Crear modelo OrderShippingSnapshot
        migrations.CreateModel(
            name='OrderShippingSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, db_column='id', verbose_name='ID')),
                ('customer_name', models.CharField(db_column='customer_name', max_length=255, verbose_name='Nombre del cliente')),
                ('customer_email', models.EmailField(db_column='customer_email', max_length=255, verbose_name='Correo del cliente')),
                ('customer_phone', models.CharField(blank=True, db_column='customer_phone', max_length=20, verbose_name='Teléfono del cliente')),
                ('shipping_street', models.CharField(db_column='shipping_street', max_length=255, verbose_name='Calle de envío')),
                ('shipping_city', models.CharField(db_column='shipping_city', max_length=100, verbose_name='Ciudad de envío')),
                ('shipping_region', models.CharField(db_column='shipping_region', max_length=100, verbose_name='Región de envío')),
                ('shipping_postal_code', models.CharField(blank=True, db_column='shipping_postal_code', max_length=20, verbose_name='Código postal')),
                ('shipping_country', models.CharField(db_column='shipping_country', default='Chile', max_length=100, verbose_name='País')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')),
                ('original_user', models.ForeignKey(blank=True, db_column='original_user_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shipping_snapshots', to='users.user', verbose_name='Usuario original')),
                ('original_address', models.ForeignKey(blank=True, db_column='original_address_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_snapshots', to='users.address', verbose_name='Dirección original')),
            ],
            options={
                'verbose_name': 'Snapshot de Envío',
                'verbose_name_plural': 'Snapshots de Envío',
                'db_table': 'order_shipping_snapshots',
            },
        ),
        
        # 2. Agregar FK a Order (nullable temporalmente)
        migrations.AddField(
            model_name='order',
            name='shipping_snapshot',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='order',
                to='orders.ordershippingsnapshot',
                db_column='shipping_snapshot_id',
                verbose_name='Snapshot de envío'
            ),
        ),
        
        # 3. Migrar datos existentes
        migrations.RunPython(migrate_existing_orders, reverse_code=migrations.RunPython.noop),
        
        # 4. Hacer FK obligatoria (solo si hay órdenes)
        # NOTA: Si no hay órdenes, esto fallará. Usaremos una migración condicional.
        # Por ahora, dejamos nullable y haremos obligatoria en migración separada si es necesario
        # migrations.AlterField(
        #     model_name='order',
        #     name='shipping_snapshot',
        #     field=models.OneToOneField(
        #         on_delete=django.db.models.deletion.PROTECT,
        #         related_name='order',
        #         to='orders.ordershippingsnapshot',
        #         db_column='shipping_snapshot_id',
        #         verbose_name='Snapshot de envío'
        #     ),
        # ),
        
        # 5. Eliminar índice de customer_email (ya no existe el campo)
        migrations.RemoveIndex(
            model_name='order',
            name='idx_order_customer_email',
        ),
        
        # 6. Eliminar campos duplicados antiguos
        migrations.RemoveField(model_name='order', name='customer_name'),
        migrations.RemoveField(model_name='order', name='customer_email'),
        migrations.RemoveField(model_name='order', name='customer_phone'),
        migrations.RemoveField(model_name='order', name='shipping_street'),
        migrations.RemoveField(model_name='order', name='shipping_city'),
        migrations.RemoveField(model_name='order', name='shipping_region'),
        migrations.RemoveField(model_name='order', name='shipping_postal_code'),
        
        # 7. Índices
        migrations.AddIndex(
            model_name='ordershippingsnapshot',
            index=models.Index(fields=['created_at'], name='idx_snapshot_created'),
        ),
        migrations.AddIndex(
            model_name='ordershippingsnapshot',
            index=models.Index(fields=['original_user'], name='idx_snapshot_user'),
        ),
    ]

