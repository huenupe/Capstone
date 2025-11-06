import decimal

import pytest

from apps.cart.models import Cart
from apps.orders.models import Order
from tests.factories import CartFactory, CartItemFactory, ProductFactory


@pytest.mark.django_db
def test_shipping_quote_allows_guest_requests(api_client):
    product = ProductFactory(price=decimal.Decimal("25000.00"))

    payload = {
        "region": "Región Metropolitana",
        "cart_items": [
            {"product_id": product.id, "quantity": 2},
        ],
        "subtotal": float(product.final_price) * 2,
    }

    response = api_client.post("/api/checkout/shipping-quote", payload, format="json")

    assert response.status_code == 200
    data = response.json()
    assert "cost" in data
    assert data["cost"] >= 0


@pytest.mark.django_db
def test_authenticated_user_can_create_order(auth_client, user, pending_status):
    product = ProductFactory(price=decimal.Decimal("19990.00"))
    cart = CartFactory(user=user, session_token=None)
    CartItemFactory(cart=cart, product=product, quantity=2)

    payload = {
        "customer_name": f"{user.first_name} {user.last_name}",
        "customer_email": user.email,
        "customer_phone": "+56911111111",
        "shipping_street": "Calle Falsa 123",
        "shipping_city": "Santiago",
        "shipping_region": "Región Metropolitana",
        "shipping_postal_code": "8320000",
    }

    response = auth_client.post("/api/orders/create", payload, format="json")

    assert response.status_code == 201, response.content
    data = response.json()
    order = Order.objects.get(id=data["id"])
    cart.refresh_from_db()

    assert order.user == user
    assert order.items.count() == 1
    assert order.status.code == "PENDING"
    assert order.shipping_city == payload["shipping_city"]
    assert cart.is_active is False


@pytest.mark.django_db
def test_guest_checkout_creates_order_with_session_token(api_client, pending_status):
    product = ProductFactory(price=decimal.Decimal("15000.00"))
    guest_token = "guest-test-token"
    cart = CartFactory(user=None, session_token=guest_token)
    CartItemFactory(cart=cart, product=product, quantity=3)

    payload = {
        "customer_name": "Invitado Tester",
        "customer_email": "guest@example.com",
        "customer_phone": "",
        "shipping_street": "Los Álamos 456",
        "shipping_city": "Concepción",
        "shipping_region": "Biobío",
        "shipping_postal_code": "4030000",
    }

    response = api_client.post(
        "/api/orders/create",
        payload,
        format="json",
        HTTP_X_SESSION_TOKEN=guest_token,
    )

    assert response.status_code == 201, response.content
    data = response.json()
    order = Order.objects.get(id=data["id"])
    cart.refresh_from_db()

    assert order.user is None
    assert order.customer_email == payload["customer_email"]
    assert order.items.count() == 1
    assert order.status.code == "PENDING"
    assert not cart.is_active


