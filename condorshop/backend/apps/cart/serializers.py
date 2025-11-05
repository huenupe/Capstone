from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'unit_price', 'subtotal')


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
        return sum(item.subtotal for item in obj.items.all())

    def get_shipping_cost(self, obj):
        """Costo de envío fijo (puede modificarse después)"""
        subtotal = self.get_subtotal(obj)
        if subtotal >= 50000:  # Envío gratis sobre 50k
            return 0
        return 5000  # Costo fijo de envío

    def get_total(self, obj):
        """Total = subtotal + shipping"""
        return self.get_subtotal(obj) + self.get_shipping_cost(obj)


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

