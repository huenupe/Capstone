import pytest

from apps.orders.models import OrderStatus
from tests.factories import ProductFactory


@pytest.mark.django_db
def test_products_prefix_filter_and_integer_prices(api_client):
    product = ProductFactory(name="Alpha Monitor", slug="alpha-monitor", price=120000, stock_qty=5, active=True)
    ProductFactory(name="Zeta Mouse", slug="zeta-mouse", price=19990, stock_qty=3, active=True)

    response = api_client.get("/api/products/?name__istartswith=alpha")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert all(item["name"].lower().startswith("alpha") for item in payload["results"])

    target = next(item for item in payload["results"] if item["slug"] == product.slug)
    assert isinstance(target["final_price"], int)
    assert target["final_price"] == product.final_price


@pytest.mark.django_db
def test_guest_cart_checkout_returns_integer_amounts(api_client):
    OrderStatus.objects.get_or_create(code="PENDING", defaults={"description": "Pendiente"})
    product = ProductFactory(price=15000, stock_qty=10, active=True)

    add_resp = api_client.post(
        "/api/cart/add",
        {"product_id": product.id, "quantity": 2},
        format="json",
    )
    assert add_resp.status_code == 201
    session_token = add_resp["X-Session-Token"]

    cart_resp = api_client.get("/api/cart/", HTTP_X_SESSION_TOKEN=session_token)
    assert cart_resp.status_code == 200
    cart_data = cart_resp.json()
    assert cart_data["items"], "El carrito debería contener items"
    item = cart_data["items"][0]
    assert isinstance(item["unit_price"], int)
    assert isinstance(item["subtotal"], int)
    for field in ("subtotal", "shipping_cost", "total"):
        assert isinstance(cart_data[field], int)

    order_payload = {
        "customer_name": "Demo Customer",
        "customer_email": "demo@example.com",
        "customer_phone": "+56911111111",
        "shipping_street": "Calle Demo 123",
        "shipping_city": "Santiago",
        "shipping_region": "Región Metropolitana",
        "shipping_postal_code": "8320000",
        "save_address": False,
    }
    order_resp = api_client.post(
        "/api/orders/create",
        order_payload,
        format="json",
        HTTP_X_SESSION_TOKEN=session_token,
    )
    assert order_resp.status_code == 201, order_resp.content
    order_data = order_resp.json()
    assert isinstance(order_data["total_amount"], int)
    assert isinstance(order_data["shipping_cost"], int)
    assert order_data["items"]
    for order_item in order_data["items"]:
        assert isinstance(order_item["unit_price"], int)
        assert isinstance(order_item["total_price"], int)

