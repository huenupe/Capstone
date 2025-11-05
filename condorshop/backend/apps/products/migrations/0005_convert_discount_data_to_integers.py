# Generated migration for data conversion
from django.db import migrations
import logging

logger = logging.getLogger(__name__)


def convert_discount_data_forward(apps, schema_editor):
    """
    Convierte valores de descuento existentes a enteros:
    - discount_percent: si está como fracción (0.XX), convertir a entero (XX)
    - discount_amount y discount_price: redondear a entero
    """
    Product = apps.get_model('products', 'Product')
    
    converted_percent = 0
    converted_amount = 0
    converted_price = 0
    normalized = 0
    
    for product in Product.objects.all():
        changed = False
        
        # Convertir discount_percent de fracción a entero (1-100)
        if product.discount_percent is not None:
            try:
                # Si es un Decimal/Float menor que 1, asumimos que es fracción (0.06 -> 6)
                if isinstance(product.discount_percent, (float,)) and product.discount_percent < 1:
                    new_percent = round(product.discount_percent * 100)
                    if 1 <= new_percent <= 100:
                        product.discount_percent = new_percent
                        converted_percent += 1
                        changed = True
                        logger.info(f"Product {product.id}: Converted discount_percent from {product.discount_percent/100 if product.discount_percent < 1 else product.discount_percent} to {new_percent}")
                # Si es un Decimal/float mayor que 1 pero menor que 100, redondear
                elif isinstance(product.discount_percent, (float,)) and 1 <= product.discount_percent <= 100:
                    new_percent = round(product.discount_percent)
                    product.discount_percent = new_percent
                    converted_percent += 1
                    changed = True
                # Si es mayor que 100, normalizar
                elif product.discount_percent > 100:
                    product.discount_percent = 100
                    normalized += 1
                    changed = True
                    logger.warning(f"Product {product.id}: Normalized discount_percent from {product.discount_percent} to 100")
                # Si es menor que 1 (y no es fracción), normalizar a 1
                elif product.discount_percent < 1:
                    product.discount_percent = 1
                    normalized += 1
                    changed = True
                    logger.warning(f"Product {product.id}: Normalized discount_percent from {product.discount_percent} to 1")
            except (TypeError, ValueError) as e:
                logger.error(f"Product {product.id}: Error converting discount_percent: {e}")
        
        # Convertir discount_amount a entero (redondear)
        if product.discount_amount is not None:
            try:
                old_amount = product.discount_amount
                new_amount = round(float(product.discount_amount))
                if new_amount != old_amount:
                    product.discount_amount = new_amount
                    converted_amount += 1
                    changed = True
                    logger.info(f"Product {product.id}: Converted discount_amount from {old_amount} to {new_amount}")
                # Validar que no sea mayor que el precio
                if product.price and new_amount > int(product.price):
                    product.discount_amount = int(product.price)
                    normalized += 1
                    changed = True
                    logger.warning(f"Product {product.id}: Normalized discount_amount to price limit")
            except (TypeError, ValueError) as e:
                logger.error(f"Product {product.id}: Error converting discount_amount: {e}")
        
        # Convertir discount_price a entero (redondear)
        if product.discount_price is not None:
            try:
                old_price = product.discount_price
                new_price = round(float(product.discount_price))
                if new_price != old_price:
                    product.discount_price = new_price
                    converted_price += 1
                    changed = True
                    logger.info(f"Product {product.id}: Converted discount_price from {old_price} to {new_price}")
                # Validar que no sea mayor que el precio original
                if product.price and new_price > int(product.price):
                    product.discount_price = int(product.price)
                    normalized += 1
                    changed = True
                    logger.warning(f"Product {product.id}: Normalized discount_price to price limit")
                # Validar que no sea negativo
                if new_price < 0:
                    product.discount_price = 0
                    normalized += 1
                    changed = True
                    logger.warning(f"Product {product.id}: Normalized discount_price from negative to 0")
            except (TypeError, ValueError) as e:
                logger.error(f"Product {product.id}: Error converting discount_price: {e}")
        
        if changed:
            product.save(update_fields=['discount_percent', 'discount_amount', 'discount_price'])
    
    logger.info(f"Migration completed: {converted_percent} discount_percent, {converted_amount} discount_amount, {converted_price} discount_price converted. {normalized} values normalized.")


def convert_discount_data_backward(apps, schema_editor):
    """
    Rollback: convertir enteros de vuelta a Decimal (no crítico, pero útil para rollback)
    """
    # No implementamos rollback completo ya que la conversión es lossy
    # Solo logueamos que se puede perder precisión
    logger.info("Rollback: Note that converting back to Decimal may lose precision")


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_normalize_discounts_to_integers'),
    ]

    operations = [
        migrations.RunPython(convert_discount_data_forward, convert_discount_data_backward),
    ]

