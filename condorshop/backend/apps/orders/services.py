"""Servicios y utilidades para el dominio de pedidos."""

from typing import Iterable, Optional, Sequence, Set

from django.conf import settings
from django.core.mail import send_mail

from apps.products.models import Product

from .models import ShippingRule, ShippingZone


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


def evaluate_shipping(region: Optional[str], subtotal, cart_items: Optional[Iterable]) -> dict:
    """
    Determinar costo de envío y metadatos relevantes reutilizables en el checkout.

    Retorna un diccionario con las llaves:
    - cost (int)
    - free_shipping_threshold (int | None)
    - zone (str | None)
    - rule_type (str)
    - applied_rule_id (int | None)
    """

    subtotal_int = _to_int(subtotal)

    if not region or not cart_items:
        cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
        return {
            "cost": cost,
            "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
            "zone": None,
            "rule_type": "DEFAULT",
            "applied_rule_id": None,
        }

    # Resolver zona
    zone = ShippingZone.objects.filter(
        is_active=True,
        regions__icontains=region,
    ).first()

    rules_qs = ShippingRule.objects.filter(is_active=True).select_related(
        "zone", "product__category", "category"
    )
    if zone:
        rules_qs = rules_qs.filter(zone__in=[zone, None])
    else:
        rules_qs = rules_qs.filter(zone__isnull=True)

    rules_qs = rules_qs.order_by("-priority", "-created_at")

    product_ids, category_ids = _extract_product_context(list(cart_items))
    product_id_set = set(product_ids)
    category_id_set = set(category_ids)

    applied_rule = None
    category_rule = None
    all_rule = None

    for rule in rules_qs:
        if rule.rule_type == "PRODUCT" and rule.product_id in product_id_set:
            applied_rule = rule
            break
        if rule.rule_type == "CATEGORY" and rule.category_id in category_id_set and category_rule is None:
            category_rule = rule
        if rule.rule_type == "ALL" and all_rule is None:
            all_rule = rule

    if not applied_rule:
        applied_rule = category_rule or all_rule

    if applied_rule:
        threshold = applied_rule.free_shipping_threshold
        if threshold and subtotal_int >= threshold:
            cost = 0
        else:
            cost = applied_rule.base_cost

        return {
            "cost": cost,
            "free_shipping_threshold": threshold,
            "zone": zone.name if zone else None,
            "rule_type": applied_rule.rule_type,
            "applied_rule_id": applied_rule.id,
        }

    # Fallback por defecto
    cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
    return {
        "cost": cost,
        "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
        "zone": zone.name if zone else None,
        "rule_type": "DEFAULT",
        "applied_rule_id": None,
    }


def send_order_confirmation_email(order):
    """
    Prepara el envío de email de confirmación de pedido
    Se completará cuando se integre Webpay
    """
    subject = f'Confirmación de pedido #{order.id} - CondorShop'
    message = f"""
    Hola {order.customer_name},

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
    #     recipient_list=[order.customer_email],
    #     fail_silently=False,
    # )

    return True

