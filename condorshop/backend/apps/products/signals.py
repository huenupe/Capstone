"""
Signals para capturar cambios de precio automáticamente en ProductPriceHistory.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Product, ProductPriceHistory


@receiver(pre_save, sender=Product)
def track_price_changes(sender, instance, **kwargs):
    """
    Detecta cambios en precios antes de guardar y marca el producto
    para crear un registro en ProductPriceHistory.
    """
    if instance.pk:  # Solo para productos existentes
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            
            # Verificar si cambió algún campo de precio
            price_changed = (
                old_instance.price != instance.price or
                old_instance.discount_price != instance.discount_price or
                old_instance.discount_amount != instance.discount_amount or
                old_instance.discount_percent != instance.discount_percent
            )
            
            if price_changed:
                # Marcar que hay un cambio de precio
                instance._price_changed = True
                instance._old_final_price = old_instance.final_price
        except Product.DoesNotExist:
            # Producto nuevo, no hay precio anterior
            instance._price_changed = False
    else:
        # Producto nuevo
        instance._price_changed = False


@receiver(post_save, sender=Product)
def create_price_history(sender, instance, created, **kwargs):
    """
    Crea un registro en ProductPriceHistory cuando se detecta un cambio de precio.
    """
    now = timezone.now()
    
    if created:
        # Producto nuevo: crear primer registro de historial
        ProductPriceHistory.objects.create(
            product=instance,
            price=instance.price,
            discount_price=instance.discount_price,
            discount_amount=instance.discount_amount,
            discount_percent=instance.discount_percent,
            final_price=instance.final_price,
            effective_from=instance.created_at or now,
            effective_to=None  # Precio actual
        )
    elif hasattr(instance, '_price_changed') and instance._price_changed:
        # Precio cambió: cerrar registro anterior y crear nuevo
        
        # 1. Cerrar el registro anterior (si existe)
        previous_history = ProductPriceHistory.objects.filter(
            product=instance,
            effective_to__isnull=True
        ).first()
        
        if previous_history:
            previous_history.effective_to = now
            previous_history.save(update_fields=['effective_to'])
        
        # 2. Crear nuevo registro con el precio actual
        ProductPriceHistory.objects.create(
            product=instance,
            price=instance.price,
            discount_price=instance.discount_price,
            discount_amount=instance.discount_amount,
            discount_percent=instance.discount_percent,
            final_price=instance.final_price,
            effective_from=now,
            effective_to=None  # Precio actual
        )

