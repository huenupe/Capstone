"""Servicios y utilidades para el dominio de pedidos."""

from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional, Sequence, Set

from django.conf import settings
from django.core.mail import send_mail

from apps.products.models import Product

from .models import ShippingRule, ShippingZone


DEFAULT_FREE_SHIPPING_THRESHOLD = Decimal("50000.00")
DEFAULT_SHIPPING_COST = Decimal("5000.00")


def _to_decimal(value) -> Decimal:
    """Convertir un valor numérico (o string) a Decimal de forma segura."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (TypeError, InvalidOperation):
        return Decimal("0.00")


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
    - cost (Decimal)
    - free_shipping_threshold (Decimal | None)
    - zone (str | None)
    - rule_type (str)
    - applied_rule_id (int | None)
    """

    subtotal_decimal = _to_decimal(subtotal)

    if not region or not cart_items:
        cost = Decimal("0.00") if subtotal_decimal >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
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

    rules = ShippingRule.objects.filter(is_active=True)
    if zone:
        rules = rules.filter(zone__in=[zone, None])
    else:
        rules = rules.filter(zone__isnull=True)

    rules = rules.order_by("-priority", "-created_at")

    product_ids, category_ids = _extract_product_context(list(cart_items))

    applied_rule = None

    if product_ids:
        product_rules = rules.filter(rule_type="PRODUCT", product_id__in=product_ids)
        if product_rules.exists():
            applied_rule = product_rules.first()

    if not applied_rule and category_ids:
        category_rules = rules.filter(rule_type="CATEGORY", category_id__in=category_ids)
        if category_rules.exists():
            applied_rule = category_rules.first()

    if not applied_rule:
        all_rules = rules.filter(rule_type="ALL")
        if all_rules.exists():
            applied_rule = all_rules.first()

    if applied_rule:
        threshold = applied_rule.free_shipping_threshold
        if threshold and subtotal_decimal >= threshold:
            cost = Decimal("0.00")
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
    cost = Decimal("0.00") if subtotal_decimal >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
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

