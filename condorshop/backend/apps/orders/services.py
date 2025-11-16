"""Servicios y utilidades para el dominio de pedidos."""

from typing import Iterable, Optional, Sequence, Set

from django.conf import settings
from django.core.mail import send_mail

from apps.products.models import Product

from .models import ShippingRule, ShippingZone, ShippingCarrier


DEFAULT_FREE_SHIPPING_THRESHOLD = 50000
DEFAULT_SHIPPING_COST = 5000


def _to_int(value) -> int:
    """Convertir un valor numérico (o string) a entero CLP con redondeo half-up."""
    if isinstance(value, int):
        return value
    if value is None:
        return 0
    value_str = str(value)
    if not value_str:
        return 0
    if '.' not in value_str:
        return int(value_str)
    integer_part, fractional_part = value_str.split('.', 1)
    fractional_part = (fractional_part + '00')[:2]
    rounded = int(integer_part or '0')
    if int(fractional_part) >= 50:
        rounded += 1
    return rounded


def _extract_product_context(cart_items: Sequence) -> tuple[list[int], Set[int]]:
    """Obtener IDs de productos y categorías desde los items del carrito."""
    product_ids: list[int] = []
    category_ids: Set[int] = set()
    missing_product_ids: Set[int] = set()

    for item in cart_items:
        product = getattr(item, "product", None)

        if isinstance(item, dict):
            product_id = item.get("product_id")
        else:
            product_id = getattr(item, "product_id", None)

        if not product_id:
            continue

        product_ids.append(product_id)

        if product and getattr(product, "category_id", None):
            category_ids.add(product.category_id)
        else:
            missing_product_ids.add(product_id)

    if missing_product_ids:
        for product in Product.objects.filter(id__in=missing_product_ids).select_related("category"):
            if product.category_id:
                category_ids.add(product.category_id)

    return product_ids, category_ids


def _calculate_total_weight(cart_items: Optional[Iterable]) -> float:
    """Calcula el peso total de los items del carrito en kg"""
    if not cart_items:
        return 0.0
    
    total_weight = 0.0
    for item in cart_items:
        product = getattr(item, "product", None)
        
        if isinstance(item, dict):
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
        else:
            product_id = getattr(item, "product_id", None)
            quantity = getattr(item, "quantity", 1)
        
        if not product_id:
            continue
        
        if not product:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
        
        weight = float(product.weight or 0)
        total_weight += weight * quantity
    
    return total_weight


def evaluate_shipping(region: Optional[str], subtotal, cart_items: Optional[Iterable]) -> dict:
    """
    Determinar costo de envío y metadatos relevantes reutilizables en el checkout.
    Usa la nueva estructura de ShippingRule con carrier, peso y criterios múltiples.

    Retorna un diccionario con las llaves:
    - cost (int)
    - free_shipping_threshold (int | None)
    - zone (str | None)
    - carrier (str | None)
    - applied_rule_id (int | None)
    """

    subtotal_int = _to_int(subtotal)
    total_weight = _calculate_total_weight(cart_items)

    if not region or not cart_items:
        cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
        return {
            "cost": cost,
            "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
            "zone": None,
            "carrier": None,
            "applied_rule_id": None,
        }

    # Resolver zona
    zone = ShippingZone.objects.filter(
        is_active=True,
        regions__icontains=region,
    ).first()

    # Obtener reglas activas ordenadas por prioridad
    rules_qs = ShippingRule.objects.filter(
        is_active=True,
        carrier__is_active=True
    ).select_related('carrier', 'zone').order_by('-priority', 'base_cost')

    # Filtrar por zona si existe
    if zone:
        rules_qs = rules_qs.filter(zone__in=[zone, None])
    else:
        rules_qs = rules_qs.filter(zone__isnull=True)

    # Buscar la primera regla que aplique
    applied_rule = None
    for rule in rules_qs:
        if rule.applies_to(zone, subtotal_int, total_weight):
            applied_rule = rule
            break

    if applied_rule:
        cost = applied_rule.calculate_cost(subtotal_int, total_weight)
        return {
            "cost": cost,
            "free_shipping_threshold": applied_rule.free_shipping_threshold,
            "zone": zone.name if zone else None,
            "carrier": applied_rule.carrier.name if applied_rule.carrier else None,
            "applied_rule_id": applied_rule.id,
        }

    # Fallback por defecto
    cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
    return {
        "cost": cost,
        "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
        "zone": zone.name if zone else None,
        "carrier": None,
        "applied_rule_id": None,
    }


def send_order_confirmation_email(order):
    """
    Prepara el envío de email de confirmación de pedido
    Se completará cuando se integre Webpay
    """
    # Obtener datos del cliente desde shipping_snapshot
    customer_name = ''
    customer_email = ''
    if order.shipping_snapshot:
        customer_name = order.shipping_snapshot.customer_name or ''
        customer_email = order.shipping_snapshot.customer_email or ''
    
    subject = f'Confirmación de pedido #{order.id} - CondorShop'
    message = f"""
    Hola {customer_name},

    Tu pedido #{order.id} ha sido confirmado.

    Total: ${order.total_amount:,.0f} CLP
    Estado: {order.status.description}

    Gracias por tu compra!

    CondorShop
    """

    # Por ahora solo prepara el email, no lo envía
    # Se implementará cuando se integre Webpay
    # send_mail(
    #     subject=subject,
    #     message=message,
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[customer_email],
    #     fail_silently=False,
    # )

    return True

