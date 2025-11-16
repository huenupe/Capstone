# Generated manually for Acción 7: Clarificar shipping_rules
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


def create_default_carrier(apps, schema_editor):
    """Crear carrier por defecto para migrar reglas existentes"""
    ShippingCarrier = apps.get_model('orders', 'ShippingCarrier')
    
    # Crear carrier por defecto si no existe
    carrier, created = ShippingCarrier.objects.get_or_create(
        code='DEFAULT',
        defaults={
            'name': 'Transportista por Defecto',
            'description': 'Carrier creado automáticamente durante migración',
            'is_active': True,
            'sort_order': 0
        }
    )
    return carrier


def migrate_shipping_rules(apps, schema_editor):
    """
    Migrar reglas existentes a la nueva estructura.
    Si hay reglas con rule_type, product, category, se migran a la nueva estructura.
    """
    ShippingRule = apps.get_model('orders', 'ShippingRule')
    ShippingCarrier = apps.get_model('orders', 'ShippingCarrier')
    
    # Obtener o crear carrier por defecto
    default_carrier = create_default_carrier(apps, schema_editor)
    
    # Verificar si hay campos antiguos (rule_type, product, category)
    # Si no existen, la migración ya fue aplicada o no hay datos
    try:
        # Intentar acceder a rule_type para verificar si existe
        old_rules = ShippingRule.objects.all()
        if old_rules.exists():
            # Si hay reglas, verificar si tienen rule_type
            first_rule = old_rules.first()
            if hasattr(first_rule, 'rule_type'):
                # Migrar reglas antiguas
                for rule in old_rules:
                    # Asignar carrier por defecto
                    rule.carrier = default_carrier
                    # Establecer valores por defecto para nuevos campos
                    rule.min_weight = Decimal('0')
                    rule.max_weight = None
                    rule.min_order_amount = 0
                    rule.cost_per_kg = 0
                    # Guardar (solo campos nuevos, los antiguos se eliminarán después)
                    ShippingRule.objects.filter(pk=rule.pk).update(
                        carrier_id=default_carrier.id,
                        min_weight=Decimal('0'),
                        max_weight=None,
                        min_order_amount=0,
                        cost_per_kg=0
                    )
    except Exception:
        # Si falla, continuar (probablemente los campos ya no existen)
        pass


def reverse_migrate_shipping_rules(apps, schema_editor):
    """Reversión: no se puede restaurar rule_type/product/category fácilmente"""
    pass


def drop_old_indexes_safely(apps, schema_editor):
    """
    Elimina índices antiguos de forma segura, verificando existencia primero.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Lista de índices antiguos a eliminar
        old_indexes = [
            'idx_rule_zone_active',
            'idx_rule_type_active',
            'idx_shiprule_type_product',
            'idx_shiprule_type_category',
        ]
        
        for index_name in old_indexes:
            try:
                # Verificar si el índice existe (sintaxis diferente por DB)
                index_exists = False
                fk_constraint = None
                
                if db_vendor == 'mysql':
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.STATISTICS 
                        WHERE table_schema = DATABASE() 
                        AND table_name = 'shipping_rules' 
                        AND index_name = %s
                    """, [index_name])
                    index_exists = cursor.fetchone()[0] > 0
                    
                    if index_exists:
                        # Verificar si el índice está en una foreign key constraint
                        cursor.execute("""
                            SELECT CONSTRAINT_NAME
                            FROM information_schema.KEY_COLUMN_USAGE
                            WHERE table_schema = DATABASE()
                            AND table_name = 'shipping_rules'
                            AND index_name = %s
                            AND REFERENCED_TABLE_NAME IS NOT NULL
                        """, [index_name])
                        fk_constraint = cursor.fetchone()
                        
                elif db_vendor == 'postgresql':
                    cursor.execute("SELECT current_schema()")
                    schema_name = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM pg_indexes 
                        WHERE schemaname = %s
                        AND tablename = 'shipping_rules' 
                        AND indexname = %s
                    """, [schema_name, index_name])
                    index_exists = cursor.fetchone()[0] > 0
                    
                    # En PostgreSQL, los índices de FK se manejan diferente
                    # No necesitamos verificar FK constraints antes de eliminar índices
                    
                else:
                    index_exists = True  # Asumir que existe
                
                if index_exists:
                    # Si hay una FK en MySQL, primero eliminar la FK
                    if db_vendor == 'mysql' and fk_constraint:
                        fk_name = fk_constraint[0]
                        try:
                            cursor.execute(f"ALTER TABLE shipping_rules DROP FOREIGN KEY `{fk_name}`")
                            print(f"[OK] Foreign key {fk_name} eliminada")
                        except Exception as fk_error:
                            print(f"[WARN] No se pudo eliminar FK {fk_name}: {fk_error}")
                    
                    # Eliminar el índice (sintaxis diferente por DB)
                    if db_vendor == 'mysql':
                        cursor.execute(f"DROP INDEX `{index_name}` ON shipping_rules")
                    elif db_vendor == 'postgresql':
                        cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                    else:
                        cursor.execute(f"DROP INDEX {index_name}")
                    print(f"[OK] Índice {index_name} eliminado")
                else:
                    print(f"[SKIP] Índice {index_name} no existe, omitiendo")
            except Exception as e:
                print(f"[WARN] Error al eliminar índice {index_name}: {e}")
                # Continuar con el siguiente índice


def drop_old_columns_safely(apps, schema_editor):
    """
    Elimina columnas antiguas de forma segura, verificando existencia y eliminando
    foreign keys primero si existen.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Columnas a eliminar con sus posibles foreign keys
        columns_to_drop = [
            ('rule_type', None),
            ('product_id', 'shipping_rules_product_id_fk'),
            ('category_id', 'shipping_rules_category_id_fk'),
        ]
        
        for column_name, fk_name in columns_to_drop:
            try:
                # Verificar si la columna existe (sintaxis diferente por DB)
                column_exists = False
                
                if db_vendor == 'mysql':
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.COLUMNS 
                        WHERE table_schema = DATABASE() 
                        AND table_name = 'shipping_rules' 
                        AND column_name = %s
                    """, [column_name])
                    column_exists = cursor.fetchone()[0] > 0
                elif db_vendor == 'postgresql':
                    cursor.execute("SELECT current_schema()")
                    schema_name = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_schema = %s
                        AND table_name = 'shipping_rules' 
                        AND column_name = %s
                    """, [schema_name, column_name])
                    column_exists = cursor.fetchone()[0] > 0
                else:
                    column_exists = True  # Asumir que existe
                
                if not column_exists:
                    print(f"[SKIP] Columna {column_name} no existe, omitiendo")
                    continue
                
                # Si hay una FK asociada, intentar eliminarla primero (solo MySQL)
                if db_vendor == 'mysql' and fk_name:
                    # Buscar el nombre real de la FK (puede variar)
                    cursor.execute("""
                        SELECT CONSTRAINT_NAME
                        FROM information_schema.KEY_COLUMN_USAGE
                        WHERE table_schema = DATABASE()
                        AND table_name = 'shipping_rules'
                        AND column_name = %s
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                    """, [column_name])
                    
                    fk_result = cursor.fetchone()
                    if fk_result:
                        actual_fk_name = fk_result[0]
                        try:
                            cursor.execute(f"ALTER TABLE shipping_rules DROP FOREIGN KEY `{actual_fk_name}`")
                            print(f"[OK] Foreign key {actual_fk_name} eliminada")
                        except Exception as fk_error:
                            print(f"[WARN] No se pudo eliminar FK {actual_fk_name}: {fk_error}")
                elif db_vendor == 'postgresql' and fk_name:
                    # En PostgreSQL, las FKs se eliminan automáticamente al eliminar la columna
                    # Pero podemos intentar eliminarla explícitamente primero
                    try:
                        cursor.execute(f"ALTER TABLE shipping_rules DROP CONSTRAINT IF EXISTS {fk_name}")
                        print(f"[OK] Constraint {fk_name} eliminada (si existía)")
                    except Exception as fk_error:
                        print(f"[WARN] No se pudo eliminar constraint {fk_name}: {fk_error}")
                
                # Eliminar la columna (sintaxis compatible)
                cursor.execute(f"ALTER TABLE shipping_rules DROP COLUMN {column_name}")
                print(f"[OK] Columna {column_name} eliminada")
                
            except Exception as e:
                print(f"[WARN] Error al eliminar columna {column_name}: {e}")
                # Continuar con la siguiente columna


def reverse_drop_old_columns(apps, schema_editor):
    """Reversión: no recreamos columnas antiguas"""
    pass


def reverse_drop_old_indexes(apps, schema_editor):
    """Reversión: no recreamos índices antiguos"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_refactor_payment_transactions_webpay'),
        ('products', '0010_add_inventory_control'),
    ]

    operations = [
        # 1. Crear ShippingCarrier
        migrations.CreateModel(
            name='ShippingCarrier',
            fields=[
                ('id', models.AutoField(db_column='id', primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='name', max_length=100, verbose_name='Nombre')),
                ('code', models.CharField(db_column='code', max_length=50, unique=True, verbose_name='Código')),
                ('description', models.TextField(blank=True, db_column='description', verbose_name='Descripción')),
                ('is_active', models.BooleanField(db_column='is_active', default=True, verbose_name='Activo')),
                ('requires_address', models.BooleanField(db_column='requires_address', default=True, verbose_name='Requiere dirección')),
                ('has_tracking', models.BooleanField(db_column='has_tracking', default=False, verbose_name='Soporta tracking')),
                ('api_enabled', models.BooleanField(db_column='api_enabled', default=False, verbose_name='API habilitada')),
                ('estimated_days_min', models.IntegerField(db_column='estimated_days_min', default=1, verbose_name='Días mínimos')),
                ('estimated_days_max', models.IntegerField(db_column='estimated_days_max', default=3, verbose_name='Días máximos')),
                ('logo', models.ImageField(blank=True, db_column='logo', null=True, upload_to='carriers/', verbose_name='Logo')),
                ('website', models.URLField(blank=True, db_column='website', verbose_name='Sitio web')),
                ('sort_order', models.IntegerField(db_column='sort_order', default=0, verbose_name='Orden')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')),
            ],
            options={
                'verbose_name': 'Transportista',
                'verbose_name_plural': 'Transportistas',
                'db_table': 'shipping_carriers',
                'ordering': ['sort_order', 'name'],
            },
        ),
        
        # 2. Agregar campos nuevos a ShippingRule (antes de eliminar los antiguos)
        migrations.AddField(
            model_name='shippingrule',
            name='carrier',
            field=models.ForeignKey(
                db_column='carrier_id',
                null=True,  # Temporal para migración
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rules',
                to='orders.shippingcarrier',
                verbose_name='Transportista'
            ),
        ),
        migrations.AddField(
            model_name='shippingrule',
            name='min_weight',
            field=models.DecimalField(
                db_column='min_weight',
                decimal_places=2,
                default=Decimal('0'),
                help_text='Peso mínimo en kg',
                max_digits=10,
                verbose_name='Peso mínimo (kg)'
            ),
        ),
        migrations.AddField(
            model_name='shippingrule',
            name='max_weight',
            field=models.DecimalField(
                blank=True,
                db_column='max_weight',
                decimal_places=2,
                help_text='Peso máximo en kg. NULL = sin límite',
                max_digits=10,
                null=True,
                verbose_name='Peso máximo (kg)'
            ),
        ),
        migrations.AddField(
            model_name='shippingrule',
            name='min_order_amount',
            field=models.PositiveIntegerField(
                db_column='min_order_amount',
                default=0,
                help_text='Monto mínimo de orden en pesos',
                verbose_name='Monto mínimo'
            ),
        ),
        migrations.AddField(
            model_name='shippingrule',
            name='cost_per_kg',
            field=models.PositiveIntegerField(
                db_column='cost_per_kg',
                default=0,
                help_text='Costo adicional por kg',
                verbose_name='Costo por kg'
            ),
        ),
        
        # 3. Migrar datos existentes
        migrations.RunPython(
            migrate_shipping_rules,
            reverse_migrate_shipping_rules
        ),
        
        # 4. Hacer carrier obligatorio
        migrations.AlterField(
            model_name='shippingrule',
            name='carrier',
            field=models.ForeignKey(
                db_column='carrier_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rules',
                to='orders.shippingcarrier',
                verbose_name='Transportista'
            ),
        ),
        
        # 5. Eliminar índices antiguos PRIMERO (usar RunPython para verificar existencia)
        migrations.RunPython(
            drop_old_indexes_safely,
            reverse_drop_old_indexes
        ),
        
        # 6. Eliminar campos antiguos de ShippingRule (usar RunPython para verificar existencia y FKs)
        migrations.RunPython(
            drop_old_columns_safely,
            reverse_drop_old_columns
        ),
        
        # 7. Agregar nuevos índices
        migrations.AddIndex(
            model_name='shippingrule',
            index=models.Index(fields=['carrier', 'zone', 'is_active'], name='idx_rule_carrier_zone'),
        ),
        
        # 8. Actualizar ordenamiento
        migrations.AlterModelOptions(
            name='shippingrule',
            options={
                'verbose_name': 'Regla de Envío',
                'verbose_name_plural': 'Reglas de Envío',
                'ordering': ['-priority', 'base_cost'],
            },
        ),
    ]

