from rest_framework import serializers

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.products.serializers import ProductListSerializer, to_int


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ('id', 'code', 'description')


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'unit_price', 'total_price')

    def get_unit_price(self, obj):
        return to_int(obj.unit_price)

    def get_total_price(self, obj):
        return to_int(obj.total_price)


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'status', 'customer_name', 'customer_email', 'customer_phone',
            'shipping_street', 'shipping_city', 'shipping_region', 'shipping_postal_code',
            'total_amount', 'shipping_cost', 'currency', 'created_at', 'updated_at', 'items'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_total_amount(self, obj):
        return to_int(obj.total_amount)

    def get_shipping_cost(self, obj):
        return to_int(obj.shipping_cost)


class CreateOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    shipping_street = serializers.CharField(max_length=200)
    shipping_city = serializers.CharField(max_length=100)
    shipping_region = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    changed_by_email = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = ('id', 'status', 'changed_at', 'changed_by_email', 'note')

    def get_changed_by_email(self, obj):
        return obj.changed_by.email if obj.changed_by else None


class OrderAdminSerializer(serializers.ModelSerializer):
    """Serializer para panel de admin con más detalles"""
    status = OrderStatusSerializer(read_only=True)
    status_id = serializers.IntegerField(write_only=True, required=False)
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.SerializerMethodField()
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'user_email', 'status', 'status_id',
            'customer_name', 'customer_email', 'customer_phone',
            'shipping_street', 'shipping_city', 'shipping_region', 'shipping_postal_code',
            'total_amount', 'shipping_cost', 'currency',
            'created_at', 'updated_at', 'items', 'status_history'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_total_amount(self, obj):
        return to_int(obj.total_amount)

    def get_shipping_cost(self, obj):
        return to_int(obj.shipping_cost)

