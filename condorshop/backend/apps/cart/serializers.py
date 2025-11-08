from decimal import Decimal

from rest_framework import serializers

from .models import Cart, CartItem
from apps.products.serializers import ProductListSerializer, to_int


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'unit_price', 'subtotal')

    def get_unit_price(self, obj):
        return to_int(obj.unit_price)

    def get_subtotal(self, obj):
        return to_int(obj.subtotal)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'subtotal', 'shipping_cost', 'total')

    def get_subtotal(self, obj):
        """Calcula el subtotal sumando todos los items"""
        total = sum((item.subtotal for item in obj.items.all()), Decimal('0'))
        return to_int(total)

    def get_shipping_cost(self, obj):
        """Costo de envío fijo (puede modificarse después)"""
        subtotal = self.get_subtotal(obj)
        if subtotal >= 50000:  # Envío gratis sobre 50k
            return 0
        return 5000  # Costo fijo de envío

    def get_total(self, obj):
        """Total = subtotal + shipping"""
        subtotal = self.get_subtotal(obj)
        shipping = self.get_shipping_cost(obj)
        return subtotal + shipping


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

