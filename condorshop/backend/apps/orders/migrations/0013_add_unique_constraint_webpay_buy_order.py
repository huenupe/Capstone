# Generated manually to add unique constraint on webpay_buy_order
# Usa SQL raw porque el campo fue agregado con SQL raw en migración 0008
from django.db import migrations


def add_unique_constraint_forward(apps, schema_editor):
    """Agrega constraint único en webpay_buy_order usando SQL raw"""
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            # PostgreSQL: Crear índice único parcial (solo cuando webpay_buy_order no es NULL)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_buy_order_unique 
                ON payment_transactions (webpay_buy_order) 
                WHERE webpay_buy_order IS NOT NULL
            """)
        elif db_vendor == 'mysql':
            # MySQL: Crear índice único (MySQL ignora NULLs automáticamente)
            cursor.execute("""
                CREATE UNIQUE INDEX idx_payment_buy_order_unique 
                ON payment_transactions (webpay_buy_order)
            """)
        else:
            # Otras bases de datos: intentar con sintaxis genérica
            try:
                cursor.execute("""
                    CREATE UNIQUE INDEX idx_payment_buy_order_unique 
                    ON payment_transactions (webpay_buy_order) 
                    WHERE webpay_buy_order IS NOT NULL
                """)
            except Exception:
                # Si falla, intentar sin WHERE
                cursor.execute("""
                    CREATE UNIQUE INDEX idx_payment_buy_order_unique 
                    ON payment_transactions (webpay_buy_order)
                """)


def remove_unique_constraint_reverse(apps, schema_editor):
    """Elimina el constraint único"""
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        if db_vendor == 'mysql':
            cursor.execute("DROP INDEX IF EXISTS idx_payment_buy_order_unique ON payment_transactions")
        else:
            cursor.execute("DROP INDEX IF EXISTS idx_payment_buy_order_unique")


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0012_add_constraints'),
    ]

    operations = [
        migrations.RunPython(
            add_unique_constraint_forward,
            remove_unique_constraint_reverse,
        ),
    ]

