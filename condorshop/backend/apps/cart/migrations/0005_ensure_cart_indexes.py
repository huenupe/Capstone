from django.db import migrations


def ensure_indexes(apps, schema_editor):
    """
    Asegura que los índices existen en cart_items.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    statements = []
    
    if db_vendor == 'mysql':
        statements = [
            (
                "idx_cartitem_cart_product",
                "CREATE INDEX idx_cartitem_cart_product ON cart_items (cart_id, product_id)",
            ),
            (
                "idx_cartitem_product",
                "CREATE INDEX idx_cartitem_product ON cart_items (product_id)",
            ),
            (
                "uq_cartitem_cart_product",
                "ALTER TABLE cart_items ADD UNIQUE KEY uq_cartitem_cart_product (cart_id, product_id)",
            ),
        ]
    elif db_vendor == 'postgresql':
        statements = [
            (
                "idx_cartitem_cart_product",
                "CREATE INDEX IF NOT EXISTS idx_cartitem_cart_product ON cart_items (cart_id, product_id)",
            ),
            (
                "idx_cartitem_product",
                "CREATE INDEX IF NOT EXISTS idx_cartitem_product ON cart_items (product_id)",
            ),
            (
                "uq_cartitem_cart_product",
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_cartitem_cart_product ON cart_items (cart_id, product_id)",
            ),
        ]
    else:
        # Sintaxis genérica (puede no funcionar en todas las DB)
        statements = [
            (
                "idx_cartitem_cart_product",
                "CREATE INDEX idx_cartitem_cart_product ON cart_items (cart_id, product_id)",
            ),
            (
                "idx_cartitem_product",
                "CREATE INDEX idx_cartitem_product ON cart_items (product_id)",
            ),
            (
                "uq_cartitem_cart_product",
                "CREATE UNIQUE INDEX uq_cartitem_cart_product ON cart_items (cart_id, product_id)",
            ),
        ]
    
    with schema_editor.connection.cursor() as cursor:
        for name, sql in statements:
            # Verificar si el índice existe (sintaxis diferente por DB)
            index_exists = False
            
            if db_vendor == 'mysql':
                cursor.execute(
                    "SHOW INDEX FROM cart_items WHERE Key_name = %s", [name]
                )
                index_exists = cursor.fetchone() is not None
            elif db_vendor == 'postgresql':
                cursor.execute(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE tablename = 'cart_items' AND indexname = %s",
                    [name]
                )
                index_exists = cursor.fetchone() is not None
            else:
                # Para otras DB, intentar crear directamente
                # Si falla, significa que ya existe
                index_exists = False
            
            if not index_exists:
                # PostgreSQL ya tiene "IF NOT EXISTS" en el SQL
                # MySQL no lo soporta, así que solo ejecutamos si no existe
                if db_vendor == 'postgresql':
                    cursor.execute(sql)
                else:
                    # Para MySQL, ejecutar sin IF NOT EXISTS
                    cursor.execute(sql)


def remove_indexes(apps, schema_editor):
    """
    Elimina los índices de cart_items.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    statements = []
    
    if db_vendor == 'mysql':
        statements = [
            ("uq_cartitem_cart_product", "ALTER TABLE cart_items DROP INDEX uq_cartitem_cart_product"),
            ("idx_cartitem_product", "DROP INDEX idx_cartitem_product ON cart_items"),
            ("idx_cartitem_cart_product", "DROP INDEX idx_cartitem_cart_product ON cart_items"),
        ]
    elif db_vendor == 'postgresql':
        statements = [
            ("uq_cartitem_cart_product", "DROP INDEX IF EXISTS uq_cartitem_cart_product"),
            ("idx_cartitem_product", "DROP INDEX IF EXISTS idx_cartitem_product"),
            ("idx_cartitem_cart_product", "DROP INDEX IF EXISTS idx_cartitem_cart_product"),
        ]
    else:
        statements = [
            ("uq_cartitem_cart_product", "DROP INDEX uq_cartitem_cart_product"),
            ("idx_cartitem_product", "DROP INDEX idx_cartitem_product"),
            ("idx_cartitem_cart_product", "DROP INDEX idx_cartitem_cart_product"),
        ]
    
    with schema_editor.connection.cursor() as cursor:
        for name, sql in statements:
            # Verificar si el índice existe antes de eliminarlo
            index_exists = False
            
            if db_vendor == 'mysql':
                cursor.execute("SHOW INDEX FROM cart_items WHERE Key_name = %s", [name])
                index_exists = cursor.fetchone() is not None
            elif db_vendor == 'postgresql':
                cursor.execute(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE tablename = 'cart_items' AND indexname = %s",
                    [name]
                )
                index_exists = cursor.fetchone() is not None
            else:
                index_exists = True  # Asumir que existe para intentar eliminarlo
            
            if index_exists:
                cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_sync_total_price_column'),
    ]

    operations = [
        migrations.RunPython(ensure_indexes, remove_indexes),
    ]

