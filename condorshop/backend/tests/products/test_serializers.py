import pytest

from apps.products.serializers import ProductListSerializer
from apps.cart.serializers import CartSerializer
from tests.factories import ProductFactory, CartItemFactory


@pytest.mark.django_db
def test_product_list_serializer_formats_price():
    product = ProductFactory(price=19990)
    data = ProductListSerializer(product).data

    assert data['price'] == 19990
    assert data['price_formatted'] == "$19.990"
    assert data['final_price_formatted'] == "$19.990"
    assert data['final_price'] == 19990
    assert data['discount_percent'] == 0


@pytest.mark.django_db
def test_cart_serializer_includes_formatted_totals():
    item = CartItemFactory(unit_price=19990, quantity=2)
    cart = item.cart

    data = CartSerializer(cart).data

    assert data['items'][0]['unit_price'] == 19990
    assert data['items'][0]['unit_price_formatted'] == "$19.990"
    assert data['items'][0]['subtotal'] == 39980
    assert data['items'][0]['subtotal_formatted'] == "$39.980"
    assert data['subtotal'] == 39980
    assert data['subtotal_formatted'] == "$39.980"
    # Default shipping 5000 porque subtotal < 50000
    assert data['shipping_cost'] == 5000
    assert data['shipping_cost_formatted'] == "$5.000"
    assert data['total'] == 44980
    assert data['total_formatted'] == "$44.980"

