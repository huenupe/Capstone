# Generated manually for Acción 6: Control de inventario
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_add_category_level_sort_order_active'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Agregar campos de inventario a Product
        migrations.AddField(
            model_name='product',
            name='stock_reserved',
            field=models.PositiveIntegerField(
                default=0,
                db_column='stock_reserved',
                verbose_name='Stock reservado',
                help_text='Cantidad de stock reservada para pedidos pendientes'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(
                default=10,
                db_column='low_stock_threshold',
                verbose_name='Umbral de stock bajo',
                help_text='Cantidad mínima antes de considerar stock bajo'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='allow_backorder',
            field=models.BooleanField(
                default=False,
                db_column='allow_backorder',
                verbose_name='Permitir backorder',
                help_text='Permitir ventas cuando no hay stock disponible'
            ),
        ),
        # Agregar constraints de inventario
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(
                condition=models.Q(stock_qty__gte=0),
                name='product_stock_qty_non_negative'
            ),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(
                condition=models.Q(stock_reserved__gte=0),
                name='product_stock_reserved_non_negative'
            ),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(
                condition=models.Q(stock_reserved__lte=models.F('stock_qty')),
                name='product_stock_reserved_lte_qty'
            ),
        ),
        # Crear modelo InventoryMovement
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.BigAutoField(db_column='id', primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(
                    choices=[
                        ('purchase', 'Compra/Ingreso'),
                        ('sale', 'Venta'),
                        ('return', 'Devolución'),
                        ('adjustment', 'Ajuste Manual'),
                        ('reserve', 'Reserva'),
                        ('release', 'Liberación de Reserva'),
                        ('damage', 'Pérdida/Daño'),
                    ],
                    db_column='movement_type',
                    max_length=20,
                    verbose_name='Tipo de movimiento'
                )),
                ('quantity_change', models.IntegerField(db_column='quantity_change', verbose_name='Cambio de cantidad')),
                ('quantity_after', models.IntegerField(db_column='quantity_after', verbose_name='Cantidad después')),
                ('reason', models.CharField(blank=True, db_column='reason', max_length=255, verbose_name='Razón')),
                ('reference_id', models.IntegerField(blank=True, db_column='reference_id', null=True, verbose_name='ID de referencia')),
                ('reference_type', models.CharField(blank=True, db_column='reference_type', max_length=50, verbose_name='Tipo de referencia')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')),
                ('product', models.ForeignKey(
                    db_column='product_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inventory_movements',
                    to='products.product',
                    verbose_name='Producto'
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    db_column='created_by_id',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='inventory_movements',
                    to='users.user',
                    verbose_name='Creado por'
                )),
            ],
            options={
                'verbose_name': 'Movimiento de Inventario',
                'verbose_name_plural': 'Movimientos de Inventario',
                'db_table': 'inventory_movements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='inventorymovement',
            index=models.Index(fields=['product', '-created_at'], name='idx_inventory_product'),
        ),
        migrations.AddIndex(
            model_name='inventorymovement',
            index=models.Index(fields=['movement_type', '-created_at'], name='idx_inventory_type'),
        ),
        migrations.AddIndex(
            model_name='inventorymovement',
            index=models.Index(fields=['reference_type', 'reference_id'], name='idx_inventory_reference'),
        ),
    ]

