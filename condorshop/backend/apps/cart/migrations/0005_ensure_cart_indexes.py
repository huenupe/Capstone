from django.db import migrations


def ensure_indexes(apps, schema_editor):
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
    with schema_editor.connection.cursor() as cursor:
        for name, sql in statements:
            cursor.execute(
                "SHOW INDEX FROM cart_items WHERE Key_name = %s", [name]
            )
            if cursor.fetchone():
                continue
            cursor.execute(sql)


def remove_indexes(apps, schema_editor):
    statements = [
        ("uq_cartitem_cart_product", "ALTER TABLE cart_items DROP INDEX uq_cartitem_cart_product"),
        ("idx_cartitem_product", "DROP INDEX idx_cartitem_product ON cart_items"),
        ("idx_cartitem_cart_product", "DROP INDEX idx_cartitem_cart_product ON cart_items"),
    ]
    with schema_editor.connection.cursor() as cursor:
        for name, sql in statements:
            cursor.execute("SHOW INDEX FROM cart_items WHERE Key_name = %s", [name])
            if cursor.fetchone():
                cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_sync_total_price_column'),
    ]

    operations = [
        migrations.RunPython(ensure_indexes, remove_indexes),
    ]

