from django.db import migrations


def ensure_total_price_column(apps, schema_editor):
    """
    Asegura que la columna total_price existe en cart_items.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Verificar si la columna existe (sintaxis diferente por DB)
        if db_vendor == 'mysql':
            cursor.execute("SHOW COLUMNS FROM cart_items LIKE 'total_price'")
            column_exists = cursor.fetchone() is not None
        elif db_vendor == 'postgresql':
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'cart_items' AND column_name = 'total_price'"
            )
            column_exists = cursor.fetchone() is not None
        else:
            # Para otras bases de datos, intentar agregar directamente
            # Si falla, significa que ya existe
            column_exists = False
        
        if not column_exists:
            # Agregar columna (sintaxis diferente por DB)
            if db_vendor == 'mysql':
                cursor.execute(
                    "ALTER TABLE cart_items "
                    "ADD COLUMN total_price int unsigned NOT NULL DEFAULT 0 AFTER unit_price"
                )
            elif db_vendor == 'postgresql':
                cursor.execute(
                    "ALTER TABLE cart_items "
                    "ADD COLUMN total_price INTEGER NOT NULL DEFAULT 0"
                )
            else:
                # Sintaxis genérica (puede no funcionar en todas las DB)
                cursor.execute(
                    "ALTER TABLE cart_items "
                    "ADD COLUMN total_price INTEGER NOT NULL DEFAULT 0"
                )
        
        # Actualizar valores existentes
        cursor.execute(
            "UPDATE cart_items "
            "SET total_price = unit_price * quantity "
            "WHERE total_price IS NULL OR total_price = 0"
        )


def drop_total_price_column(apps, schema_editor):
    """
    Elimina la columna total_price de cart_items.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        # Verificar si la columna existe
        if db_vendor == 'mysql':
            cursor.execute("SHOW COLUMNS FROM cart_items LIKE 'total_price'")
            column_exists = cursor.fetchone() is not None
        elif db_vendor == 'postgresql':
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'cart_items' AND column_name = 'total_price'"
            )
            column_exists = cursor.fetchone() is not None
        else:
            column_exists = True  # Asumir que existe para intentar eliminarla
        
        if column_exists:
            cursor.execute("ALTER TABLE cart_items DROP COLUMN total_price")


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_alter_cartitem_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_total_price_column, drop_total_price_column),
    ]
