import pytest

from apps.cart.models import Cart
from apps.orders.models import Order, OrderShippingSnapshot, OrderItemSnapshot
from tests.factories import CartFactory, CartItemFactory, ProductFactory


@pytest.mark.django_db
def test_shipping_quote_allows_guest_requests(api_client):
    product = ProductFactory(price=25000)

    payload = {
        "region": "Región Metropolitana",
        "cart_items": [
            {"product_id": product.id, "quantity": 2},
        ],
        "subtotal": product.final_price * 2,
    }

    response = api_client.post("/api/checkout/shipping-quote", payload, format="json")

    assert response.status_code == 200
    data = response.json()
    assert "cost" in data
    assert data["cost"] >= 0


@pytest.mark.django_db
def test_authenticated_user_can_create_order(auth_client, user, pending_status):
    product = ProductFactory(price=19990)
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
    # Validar que existe shipping_snapshot
    assert order.shipping_snapshot is not None
    assert order.shipping_snapshot.shipping_city == payload["shipping_city"]
    assert order.shipping_snapshot.customer_email == payload["customer_email"]
    assert cart.is_active is False


@pytest.mark.django_db
def test_guest_checkout_creates_order_with_session_token(api_client, pending_status):
    product = ProductFactory(price=15000)
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
    # Validar que existe shipping_snapshot
    assert order.shipping_snapshot is not None
    assert order.shipping_snapshot.customer_email == payload["customer_email"]
    assert order.shipping_snapshot.customer_name == payload["customer_name"]
    assert order.shipping_snapshot.shipping_city == payload["shipping_city"]
    assert order.items.count() == 1
    assert order.status.code == "PENDING"
    assert not cart.is_active


@pytest.mark.django_db
def test_order_creates_shipping_snapshot(auth_client, user, pending_status):
    """Validar que al crear una orden se crea OrderShippingSnapshot con los datos correctos."""
    product = ProductFactory(price=25000)
    cart = CartFactory(user=user, session_token=None)
    CartItemFactory(cart=cart, product=product, quantity=1)

    payload = {
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_phone": "+56912345678",
        "shipping_street": "Av. Test 123",
        "shipping_city": "Valparaíso",
        "shipping_region": "Valparaíso",
        "shipping_postal_code": "2340000",
    }

    response = auth_client.post("/api/orders/create", payload, format="json")
    assert response.status_code == 201

    order = Order.objects.get(id=response.json()["id"])
    
    # Validar que existe el snapshot
    assert order.shipping_snapshot is not None
    snapshot = order.shipping_snapshot
    
    # Validar datos del snapshot
    assert snapshot.customer_name == payload["customer_name"]
    assert snapshot.customer_email == payload["customer_email"]
    assert snapshot.customer_phone == payload["customer_phone"]
    assert snapshot.shipping_street == payload["shipping_street"]
    assert snapshot.shipping_city == payload["shipping_city"]
    assert snapshot.shipping_region == payload["shipping_region"]
    assert snapshot.shipping_postal_code == payload["shipping_postal_code"]
    assert snapshot.original_user == user


@pytest.mark.django_db
def test_order_creates_item_snapshots(auth_client, user, pending_status):
    """Validar que al crear una orden se crean OrderItemSnapshot para cada item."""
    product = ProductFactory(price=19990, name="Test Product", sku="TEST-001")
    cart = CartFactory(user=user, session_token=None)
    CartItemFactory(cart=cart, product=product, quantity=2)

    payload = {
        "customer_name": f"{user.first_name} {user.last_name}",
        "customer_email": user.email,
        "customer_phone": "+56911111111",
        "shipping_street": "Calle Test 456",
        "shipping_city": "Santiago",
        "shipping_region": "Región Metropolitana",
        "shipping_postal_code": "8320000",
    }

    response = auth_client.post("/api/orders/create", payload, format="json")
    assert response.status_code == 201

    order = Order.objects.get(id=response.json()["id"])
    order_item = order.items.first()
    
    # Validar que existe el snapshot del item
    assert order_item.price_snapshot is not None
    snapshot = order_item.price_snapshot
    
    # Validar datos del snapshot
    assert snapshot.product_name == product.name
    assert snapshot.product_sku == product.sku
    assert snapshot.product_id == product.id
    assert snapshot.unit_price == product.final_price
    assert snapshot.total_price == product.final_price * 2
    assert snapshot.product_brand == product.brand


@pytest.mark.django_db
def test_order_serializer_returns_snapshot_data(auth_client, user, pending_status):
    """Validar que el serializer retorna datos desde shipping_snapshot."""
    product = ProductFactory(price=15000)
    cart = CartFactory(user=user, session_token=None)
    CartItemFactory(cart=cart, product=product, quantity=1)

    payload = {
        "customer_name": "Serializer Test",
        "customer_email": "serializer@example.com",
        "customer_phone": "+56999999999",
        "shipping_street": "Calle Serializer 789",
        "shipping_city": "Concepción",
        "shipping_region": "Biobío",
        "shipping_postal_code": "4030000",
    }

    response = auth_client.post("/api/orders/create", payload, format="json")
    assert response.status_code == 201

    data = response.json()
    
    # Validar que los campos vienen del snapshot
    assert data["customer_name"] == payload["customer_name"]
    assert data["customer_email"] == payload["customer_email"]
    assert data["customer_phone"] == payload["customer_phone"]
    assert data["shipping_street"] == payload["shipping_street"]
    assert data["shipping_city"] == payload["shipping_city"]
    assert data["shipping_region"] == payload["shipping_region"]
    assert data["shipping_postal_code"] == payload["shipping_postal_code"]


@pytest.mark.django_db
def test_order_item_serializer_returns_snapshot_data(auth_client, user, pending_status):
    """Validar que OrderItemSerializer retorna datos desde price_snapshot."""
    product = ProductFactory(price=30000, name="Snapshot Product", sku="SNAP-001")
    cart = CartFactory(user=user, session_token=None)
    CartItemFactory(cart=cart, product=product, quantity=3)

    payload = {
        "customer_name": f"{user.first_name} {user.last_name}",
        "customer_email": user.email,
        "customer_phone": "",
        "shipping_street": "Test Street",
        "shipping_city": "Test City",
        "shipping_region": "Test Region",
        "shipping_postal_code": "",
    }

    response = auth_client.post("/api/orders/create", payload, format="json")
    assert response.status_code == 201

    data = response.json()
    order_item = data["items"][0]
    
    # Validar que los campos vienen del snapshot
    assert order_item["product_name_snapshot"] == product.name
    assert order_item["product_sku_snapshot"] == product.sku
    assert isinstance(order_item["unit_price"], int)
    assert isinstance(order_item["total_price"], int)
    assert order_item["unit_price"] == product.final_price
    assert order_item["total_price"] == product.final_price * 3


