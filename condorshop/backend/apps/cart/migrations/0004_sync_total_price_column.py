from django.db import migrations


def ensure_total_price_column(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM cart_items LIKE 'total_price'")
        column_exists = cursor.fetchone() is not None
        if not column_exists:
            cursor.execute(
                "ALTER TABLE cart_items "
                "ADD COLUMN total_price int unsigned NOT NULL DEFAULT 0 AFTER unit_price"
            )
        cursor.execute(
            "UPDATE cart_items "
            "SET total_price = unit_price * quantity "
            "WHERE total_price IS NULL OR total_price = 0"
        )


def drop_total_price_column(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM cart_items LIKE 'total_price'")
        column_exists = cursor.fetchone() is not None
        if column_exists:
            cursor.execute("ALTER TABLE cart_items DROP COLUMN total_price")


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_alter_cartitem_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_total_price_column, drop_total_price_column),
    ]

