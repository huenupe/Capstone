# Generated manually for Acción 8: Corregir inconsistencia de nombres de índices
from django.db import migrations


def rename_index_safely(apps, schema_editor):
    """
    Renombra el índice de idx_order_status_created a idx_orders_status_created
    para mantener consistencia con otros índices (idx_orders_*).
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Verificar si existe el índice con el nombre antiguo
        old_exists = False
        new_exists = False
        
        if db_vendor == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.STATISTICS 
                WHERE table_schema = DATABASE() 
                AND table_name = 'orders' 
                AND index_name = 'idx_order_status_created'
            """)
            old_exists = cursor.fetchone()[0] > 0
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.STATISTICS 
                WHERE table_schema = DATABASE() 
                AND table_name = 'orders' 
                AND index_name = 'idx_orders_status_created'
            """)
            new_exists = cursor.fetchone()[0] > 0
        elif db_vendor == 'postgresql':
            # Obtener el schema actual
            cursor.execute("SELECT current_schema()")
            schema_name = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = %s
                AND tablename = 'orders' 
                AND indexname = 'idx_order_status_created'
            """, [schema_name])
            old_exists = cursor.fetchone()[0] > 0
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = %s
                AND tablename = 'orders' 
                AND indexname = 'idx_orders_status_created'
            """, [schema_name])
            new_exists = cursor.fetchone()[0] > 0
        else:
            # Para otras DB, asumir que no existe
            old_exists = False
            new_exists = False
        
        if old_exists and not new_exists:
            # Renombrar el índice (sintaxis diferente por DB)
            if db_vendor == 'mysql':
                cursor.execute("ALTER TABLE orders RENAME INDEX idx_order_status_created TO idx_orders_status_created")
            elif db_vendor == 'postgresql':
                cursor.execute("ALTER INDEX idx_order_status_created RENAME TO idx_orders_status_created")
            else:
                # Para otras DB, intentar sintaxis genérica
                cursor.execute("ALTER INDEX idx_order_status_created RENAME TO idx_orders_status_created")
            print("[OK] Índice renombrado de idx_order_status_created a idx_orders_status_created")
        elif new_exists:
            print("[SKIP] Índice ya existe con el nombre correcto (idx_orders_status_created)")
        else:
            print("[SKIP] Índice no existe, probablemente no se aplicó la migración anterior")


def reverse_rename_index(apps, schema_editor):
    """
    Reversión: renombrar de vuelta al nombre original.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        index_exists = False
        
        if db_vendor == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.STATISTICS 
                WHERE table_schema = DATABASE() 
                AND table_name = 'orders' 
                AND index_name = 'idx_orders_status_created'
            """)
            index_exists = cursor.fetchone()[0] > 0
        elif db_vendor == 'postgresql':
            cursor.execute("SELECT current_schema()")
            schema_name = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = %s
                AND tablename = 'orders' 
                AND indexname = 'idx_orders_status_created'
            """, [schema_name])
            index_exists = cursor.fetchone()[0] > 0
        else:
            index_exists = True  # Asumir que existe
        
        if index_exists:
            if db_vendor == 'mysql':
                cursor.execute("ALTER TABLE orders RENAME INDEX idx_orders_status_created TO idx_order_status_created")
            elif db_vendor == 'postgresql':
                cursor.execute("ALTER INDEX idx_orders_status_created RENAME TO idx_order_status_created")
            else:
                cursor.execute("ALTER INDEX idx_orders_status_created RENAME TO idx_order_status_created")
            print("[OK] Índice renombrado de vuelta a idx_order_status_created")


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_add_performance_indexes'),
    ]

    operations = [
        migrations.RunPython(
            rename_index_safely,
            reverse_rename_index
        ),
    ]
