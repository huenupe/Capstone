# Generated manually for Acción 4: Poblar historial inicial
from django.db import migrations
from django.utils import timezone


def populate_initial_price_history(apps, schema_editor):
    """
    Crea registros iniciales en ProductPriceHistory para todos los productos existentes.
    Usa created_at del producto como effective_from.
    """
    Product = apps.get_model('products', 'Product')
    ProductPriceHistory = apps.get_model('products', 'ProductPriceHistory')
    
    products = Product.objects.all()
    created_count = 0
    
    for product in products:
        # Calcular precio final (mismo cálculo que en el modelo)
        base = int(product.price or 0)
        final_price = base
        
        if product.discount_price is not None:
            final_price = max(int(product.discount_price), 0)
        elif product.discount_amount is not None:
            final_price = max(base - int(product.discount_amount), 0)
        elif product.discount_percent is not None:
            pct = int(product.discount_percent)
            discount = (base * pct + 50) // 100
            final_price = max(base - discount, 0)
        
        # Crear registro de historial
        ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            discount_price=product.discount_price,
            discount_amount=product.discount_amount,
            discount_percent=product.discount_percent,
            final_price=final_price,
            effective_from=product.created_at or timezone.now(),
            effective_to=None  # Precio actual
        )
        created_count += 1
    
    print(f"[OK] Creados {created_count} registros iniciales en ProductPriceHistory")


def reverse_populate_initial_price_history(apps, schema_editor):
    """
    Elimina todos los registros de historial (solo para reversión de migración).
    """
    ProductPriceHistory = apps.get_model('products', 'ProductPriceHistory')
    deleted_count = ProductPriceHistory.objects.all().delete()[0]
    print(f"[OK] Eliminados {deleted_count} registros de ProductPriceHistory")


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_create_product_price_history'),
    ]

    operations = [
        migrations.RunPython(
            populate_initial_price_history,
            reverse_populate_initial_price_history
        ),
    ]

