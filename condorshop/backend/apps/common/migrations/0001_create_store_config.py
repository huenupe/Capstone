# Generated manually for refactoring - Acción 10: Tabla de configuración

from django.db import migrations, models
import django.db.models.deletion


def create_initial_config(apps, schema_editor):
    """Crea configuraciones iniciales del sistema"""
    StoreConfig = apps.get_model('common', 'StoreConfig')
    
    configs = [
        {
            'key': 'tax_rate',
            'value': '19',
            'data_type': 'int',
            'description': 'Tasa de IVA en Chile (%)',
            'is_public': True
        },
        {
            'key': 'free_shipping_threshold',
            'value': '50000',
            'data_type': 'int',
            'description': 'Monto mínimo para envío gratis (CLP)',
            'is_public': True
        },
        {
            'key': 'currency',
            'value': 'CLP',
            'data_type': 'string',
            'description': 'Moneda del sistema',
            'is_public': True
        },
        {
            'key': 'maintenance_mode',
            'value': 'false',
            'data_type': 'boolean',
            'description': 'Modo mantención (desactiva tienda)',
            'is_public': True
        },
        {
            'key': 'stock_reservation_timeout',
            'value': '30',
            'data_type': 'int',
            'description': 'Minutos antes de liberar reserva de stock',
            'is_public': False
        },
        {
            'key': 'max_items_per_order',
            'value': '50',
            'data_type': 'int',
            'description': 'Cantidad máxima de items por orden',
            'is_public': False
        },
    ]
    
    for config in configs:
        StoreConfig.objects.get_or_create(
            key=config['key'],
            defaults=config
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreConfig',
            fields=[
                ('key', models.CharField(db_column='key', max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='Clave')),
                ('value', models.TextField(db_column='value', verbose_name='Valor')),
                ('data_type', models.CharField(choices=[('string', 'Texto'), ('int', 'Número Entero'), ('decimal', 'Número Decimal'), ('boolean', 'Booleano'), ('json', 'JSON')], db_column='data_type', default='string', max_length=20, verbose_name='Tipo de dato')),
                ('description', models.TextField(blank=True, db_column='description', help_text='Descripción de qué hace este parámetro', verbose_name='Descripción')),
                ('is_public', models.BooleanField(db_column='is_public', default=False, help_text='Si es True, puede exponerse en API pública', verbose_name='Público')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')),
                ('updated_by', models.ForeignKey(blank=True, db_column='updated_by_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='config_changes', to='users.user', verbose_name='Actualizado por')),
            ],
            options={
                'verbose_name': 'Configuración',
                'verbose_name_plural': 'Configuraciones',
                'db_table': 'store_config',
            },
        ),
        migrations.RunPython(create_initial_config, reverse_code=migrations.RunPython.noop),
    ]

