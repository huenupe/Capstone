from rest_framework import serializers

from apps.common.utils import format_clp
from .models import Cart, CartItem
from apps.products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    unit_price = serializers.IntegerField(read_only=True)
    subtotal = serializers.IntegerField(source='total_price', read_only=True)
    unit_price_formatted = serializers.SerializerMethodField()
    subtotal_formatted = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            'id',
            'product',
            'quantity',
            'unit_price',
            'subtotal',
            'unit_price_formatted',
            'subtotal_formatted',
        )

    def get_unit_price_formatted(self, obj):
        return format_clp(obj.unit_price)

    def get_subtotal_formatted(self, obj):
        return format_clp(obj.subtotal)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    subtotal_formatted = serializers.SerializerMethodField()
    shipping_cost_formatted = serializers.SerializerMethodField()
    total_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            'id',
            'items',
            'subtotal',
            'shipping_cost',
            'total',
            'subtotal_formatted',
            'shipping_cost_formatted',
            'total_formatted',
        )

    def get_subtotal(self, obj):
        """Calcula el subtotal sumando todos los items"""
        return sum(item.total_price for item in obj.items.all())

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

    def get_subtotal_formatted(self, obj):
        return format_clp(self.get_subtotal(obj))

    def get_shipping_cost_formatted(self, obj):
        return format_clp(self.get_shipping_cost(obj))

    def get_total_formatted(self, obj):
        return format_clp(self.get_total(obj))


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

