from rest_framework import serializers

from apps.common.utils import format_clp
from .models import Order, OrderItem, OrderStatus, OrderStatusHistory, PaymentTransaction
from apps.products.serializers import ProductListSerializer


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ('id', 'code', 'description')


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    # Precios desde snapshot si existe, sino desde el item
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    unit_price_formatted = serializers.SerializerMethodField()
    total_price_formatted = serializers.SerializerMethodField()
    # Información del producto desde snapshot (para historial)
    product_name_snapshot = serializers.SerializerMethodField()
    product_sku_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            'id',
            'product',
            'quantity',
            'unit_price',
            'total_price',
            'unit_price_formatted',
            'total_price_formatted',
            'product_name_snapshot',
            'product_sku_snapshot',
        )

    def get_unit_price(self, obj):
        """Obtener precio unitario desde snapshot si existe, sino desde el item."""
        if obj.price_snapshot:
            return obj.price_snapshot.unit_price
        return obj.unit_price

    def get_total_price(self, obj):
        """Obtener precio total desde snapshot si existe, sino desde el item."""
        if obj.price_snapshot:
            return obj.price_snapshot.total_price
        return obj.total_price

    def get_unit_price_formatted(self, obj):
        unit_price = self.get_unit_price(obj)
        return format_clp(unit_price)

    def get_total_price_formatted(self, obj):
        total_price = self.get_total_price(obj)
        return format_clp(total_price)
    
    def get_product_name_snapshot(self, obj):
        """Obtener nombre del producto desde snapshot si existe."""
        if obj.price_snapshot:
            return obj.price_snapshot.product_name
        return obj.product.name if obj.product else None
    
    def get_product_sku_snapshot(self, obj):
        """Obtener SKU del producto desde snapshot si existe."""
        if obj.price_snapshot:
            return obj.price_snapshot.product_sku
        return obj.product.sku if obj.product and hasattr(obj.product, 'sku') else None


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.IntegerField(read_only=True)
    shipping_cost = serializers.IntegerField(read_only=True)
    total_amount_formatted = serializers.SerializerMethodField()
    shipping_cost_formatted = serializers.SerializerMethodField()
    
    # Mantener campos en respuesta para compatibilidad con frontend
    # Estos campos ahora vienen del shipping_snapshot
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    shipping_street = serializers.SerializerMethodField()
    shipping_city = serializers.SerializerMethodField()
    shipping_region = serializers.SerializerMethodField()
    shipping_postal_code = serializers.SerializerMethodField()
    
    def get_customer_name(self, obj):
        return obj.shipping_snapshot.customer_name if obj.shipping_snapshot else ''
    
    def get_customer_email(self, obj):
        return obj.shipping_snapshot.customer_email if obj.shipping_snapshot else ''
    
    def get_customer_phone(self, obj):
        return obj.shipping_snapshot.customer_phone if obj.shipping_snapshot else ''
    
    def get_shipping_street(self, obj):
        return obj.shipping_snapshot.shipping_street if obj.shipping_snapshot else ''
    
    def get_shipping_city(self, obj):
        return obj.shipping_snapshot.shipping_city if obj.shipping_snapshot else ''
    
    def get_shipping_region(self, obj):
        return obj.shipping_snapshot.shipping_region if obj.shipping_snapshot else ''
    
    def get_shipping_postal_code(self, obj):
        return obj.shipping_snapshot.shipping_postal_code if obj.shipping_snapshot else ''

    class Meta:
        model = Order
        fields = (
            'id',
            'status',
            'customer_name',
            'customer_email',
            'customer_phone',
            'shipping_street',
            'shipping_city',
            'shipping_region',
            'shipping_postal_code',
            'total_amount',
            'shipping_cost',
            'currency',
            'created_at',
            'updated_at',
            'items',
            'total_amount_formatted',
            'shipping_cost_formatted',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_total_amount_formatted(self, obj):
        return format_clp(obj.total_amount)

    def get_shipping_cost_formatted(self, obj):
        return format_clp(obj.shipping_cost)


class CreateOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    shipping_street = serializers.CharField(max_length=200)
    shipping_city = serializers.CharField(max_length=100)
    shipping_region = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    save_address = serializers.BooleanField(required=False, default=False)
    address_label = serializers.CharField(max_length=100, required=False, allow_blank=True)


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
    total_amount = serializers.IntegerField(read_only=True)
    shipping_cost = serializers.IntegerField(read_only=True)
    total_amount_formatted = serializers.SerializerMethodField()
    shipping_cost_formatted = serializers.SerializerMethodField()
    
    # Campos desde shipping_snapshot para compatibilidad
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    shipping_street = serializers.SerializerMethodField()
    shipping_city = serializers.SerializerMethodField()
    shipping_region = serializers.SerializerMethodField()
    shipping_postal_code = serializers.SerializerMethodField()
    
    def get_customer_name(self, obj):
        return obj.shipping_snapshot.customer_name if obj.shipping_snapshot else ''
    
    def get_customer_email(self, obj):
        return obj.shipping_snapshot.customer_email if obj.shipping_snapshot else ''
    
    def get_customer_phone(self, obj):
        return obj.shipping_snapshot.customer_phone if obj.shipping_snapshot else ''
    
    def get_shipping_street(self, obj):
        return obj.shipping_snapshot.shipping_street if obj.shipping_snapshot else ''
    
    def get_shipping_city(self, obj):
        return obj.shipping_snapshot.shipping_city if obj.shipping_snapshot else ''
    
    def get_shipping_region(self, obj):
        return obj.shipping_snapshot.shipping_region if obj.shipping_snapshot else ''
    
    def get_shipping_postal_code(self, obj):
        return obj.shipping_snapshot.shipping_postal_code if obj.shipping_snapshot else ''

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'user_email',
            'status',
            'status_id',
            'customer_name',
            'customer_email',
            'customer_phone',
            'shipping_street',
            'shipping_city',
            'shipping_region',
            'shipping_postal_code',
            'total_amount',
            'shipping_cost',
            'currency',
            'created_at',
            'updated_at',
            'items',
            'status_history',
            'total_amount_formatted',
            'shipping_cost_formatted',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_total_amount_formatted(self, obj):
        return format_clp(obj.total_amount)

    def get_shipping_cost_formatted(self, obj):
        return format_clp(obj.shipping_cost)


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer para transacciones de pago (solo campos seguros)"""
    masked_card = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'order',
            'payment_method',
            'payment_method_display',
            'status',
            'status_display',
            'amount',
            'currency',
            'masked_card',
            'card_brand',
            'webpay_authorization_code',
            'webpay_transaction_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_masked_card(self, obj):
        """Retorna tarjeta enmascarada: **** 1234"""
        if obj.card_last_four:
            brand = f" ({obj.card_brand})" if obj.card_brand else ""
            return f"**** {obj.card_last_four}{brand}"
        return None
