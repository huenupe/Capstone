"""
Signals para capturar cambios de precio automáticamente en ProductPriceHistory
y invalidar caché cuando cambian productos o categorías.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from .models import Product, ProductPriceHistory, Category


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
    
    # Invalidar caché de productos después de crear/actualizar
    _invalidate_product_cache()


@receiver(post_delete, sender=Product)
def invalidate_cache_on_product_delete(sender, instance, **kwargs):
    """Invalidar caché cuando se elimina un producto"""
    _invalidate_product_cache()


def _invalidate_product_cache():
    """
    Invalida todas las claves de caché relacionadas con productos.
    El decorator @cache_page de Django crea claves basadas en la URL completa,
    por lo que necesitamos usar un patrón para invalidar todas las variaciones.
    """
    # Invalidar caché específica de productos
    cache.delete_many([
        'products_list',
        'products_active_list',
    ])
    
    # Invalidar caché de páginas (cache_page usa claves como:
    # 'views.decorators.cache.cache_page..GET.abc123...')
    # Como no podemos predecir todas las variaciones, usamos un método más directo:
    # Limpiar por patrón si usamos Redis (mejor rendimiento)
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        # Buscar y eliminar todas las claves que empiecen con 'condorshop:views.decorators.cache.cache_page'
        pattern = 'condorshop:views.decorators.cache.cache_page.*/api/products*'
        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
    except Exception:
        # Si no hay Redis o falla, invalidar caché completo solo de productos
        # Usar un enfoque más conservador: limpiar solo las claves conocidas
        pass


@receiver(post_save, sender=Category)
def invalidate_cache_on_category_change(sender, instance, **kwargs):
    """Invalidar caché cuando se crea/actualiza una categoría"""
    cache.delete_many([
        'categories_list',
        'products_list',  # También invalidar productos ya que pueden filtrarse por categoría
        'products_active_list',
    ])
    
    # Invalidar caché de páginas de categorías
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        pattern = 'condorshop:views.decorators.cache.cache_page.*/api/products/categories*'
        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
    except Exception:
        pass


@receiver(post_delete, sender=Category)
def invalidate_cache_on_category_delete(sender, instance, **kwargs):
    """Invalidar caché cuando se elimina una categoría"""
    cache.delete_many([
        'categories_list',
        'products_list',
        'products_active_list',
    ])
    
    # Invalidar caché de páginas de categorías
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        pattern = 'condorshop:views.decorators.cache.cache_page.*/api/products/categories*'
        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
    except Exception:
        pass

