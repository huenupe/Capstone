# Generated manually for Acción 4: ProductPriceHistory
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_add_category_hierarchy'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPriceHistory',
            fields=[
                ('id', models.BigAutoField(db_column='id', primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.PositiveIntegerField(db_column='price', verbose_name='Precio base')),
                ('discount_price', models.PositiveIntegerField(blank=True, db_column='discount_price', null=True, verbose_name='Precio final del descuento')),
                ('discount_amount', models.PositiveIntegerField(blank=True, db_column='discount_amount', null=True, verbose_name='Monto a descontar')),
                ('discount_percent', models.PositiveSmallIntegerField(blank=True, db_column='discount_percent', null=True, verbose_name='Descuento por porcentaje (%)')),
                ('final_price', models.PositiveIntegerField(db_column='final_price', help_text='Precio final calculado al momento del cambio', verbose_name='Precio final')),
                ('effective_from', models.DateTimeField(db_column='effective_from', help_text='Fecha y hora en que este precio entró en vigencia', verbose_name='Vigente desde')),
                ('effective_to', models.DateTimeField(blank=True, db_column='effective_to', help_text='Fecha y hora en que este precio dejó de estar vigente (NULL = precio actual)', null=True, verbose_name='Vigente hasta')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')),
                ('product', models.ForeignKey(db_column='product_id', on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='products.product', verbose_name='Producto')),
            ],
            options={
                'verbose_name': 'Historial de Precio',
                'verbose_name_plural': 'Historial de Precios',
                'db_table': 'product_price_history',
                'ordering': ['-effective_from'],
            },
        ),
        migrations.AddIndex(
            model_name='productpricehistory',
            index=models.Index(fields=['product', 'effective_from'], name='idx_price_history_product_date'),
        ),
        migrations.AddIndex(
            model_name='productpricehistory',
            index=models.Index(fields=['product', 'effective_to'], name='idx_price_history_product_to'),
        ),
        migrations.AddIndex(
            model_name='productpricehistory',
            index=models.Index(fields=['effective_from'], name='idx_price_history_from'),
        ),
        migrations.AddIndex(
            model_name='productpricehistory',
            index=models.Index(fields=['effective_to'], name='idx_price_history_to'),
        ),
    ]

