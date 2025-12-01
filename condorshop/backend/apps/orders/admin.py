from django.contrib import admin
from django.db.models import Prefetch
from .models import (
    Order, OrderItem, OrderStatus, OrderStatusHistory,
    Payment, PaymentTransaction, PaymentStatus,
    ShippingZone, ShippingCarrier, ShippingRule, OrderShippingSnapshot, OrderItemSnapshot
)


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    
    def code(self, obj):
        return obj.code
    code.short_description = 'Código'
    code.admin_order_field = 'code'
    
    def description(self, obj):
        return obj.description or '-'
    description.short_description = 'Descripción'
    description.admin_order_field = 'description'


@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    
    def code(self, obj):
        return obj.code
    code.short_description = 'Código'
    code.admin_order_field = 'code'
    
    def description(self, obj):
        return obj.description or '-'
    description.short_description = 'Descripción'
    description.admin_order_field = 'description'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    verbose_name = 'Item'
    verbose_name_plural = 'Items'
    readonly_fields = ('product', 'quantity', 'unit_price', 'total_price')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    verbose_name = 'Historial'
    verbose_name_plural = 'Historial'
    readonly_fields = ('status', 'changed_at', 'changed_by', 'note')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'customer_email', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('shipping_snapshot__customer_email', 'shipping_snapshot__customer_name', 'id')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimizar queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'status', 'shipping_snapshot')
    
    def customer_email(self, obj):
        return obj.shipping_snapshot.customer_email if obj.shipping_snapshot else 'Sin snapshot'
    customer_email.short_description = 'Correo electrónico'
    customer_email.admin_order_field = 'shipping_snapshot__customer_email'
    
    def status(self, obj):
        return obj.status.code if obj.status else '-'
    status.short_description = 'Estado'
    status.admin_order_field = 'status__code'
    
    def total_amount(self, obj):
        return f"${obj.total_amount:,.0f}".replace(',', '.')
    total_amount.short_description = 'Monto total'
    total_amount.admin_order_field = 'total_amount'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'amount_display', 'current_transaction_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__shipping_snapshot__customer_email',)
    
    def get_queryset(self, request):
        """Optimizar queries con select_related y prefetch_related"""
        qs = super().get_queryset(request)
        # PaymentTransaction ahora se relaciona con Order, no con Payment
        # Accedemos a través de order.payment_transactions
        # ✅ CORRECCIÓN: Excluir gateway_response del prefetch para evitar errores de deserialización
        # cuando hay datos corruptos (dict en lugar de JSON string)
        payment_transactions_qs = PaymentTransaction.objects.defer('gateway_response')
        return qs.select_related('order', 'status').prefetch_related(
            Prefetch('order__payment_transactions', queryset=payment_transactions_qs)
        )
    
    def status(self, obj):
        return obj.status.code if obj.status else '-'
    status.short_description = 'Estado'
    status.admin_order_field = 'status__code'
    
    def amount_display(self, obj):
        """Mostrar monto desde la transacción (propiedad)"""
        amount = obj.amount
        if amount is None:
            return '-'
        return f"${amount:,.0f}".replace(',', '.')
    amount_display.short_description = 'Monto'
    # No se puede ordenar por propiedad, solo por campos de BD
    
    def current_transaction_display(self, obj):
        """Mostrar información de la transacción actual"""
        tx = obj.current_transaction
        if tx:
            # ✅ CORRECCIÓN: buy_order era el campo antiguo y fue reemplazado por webpay_buy_order
            # después de la refactorización de Webpay (migración 0008_refactor_payment_transactions_webpay)
            return f"{tx.webpay_buy_order or 'N/A'} - {tx.status or 'N/A'}"
        return 'Sin transacciones'
    current_transaction_display.short_description = 'Transacción actual'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_method', 'status', 'amount_display', 'card_info', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('webpay_buy_order', 'webpay_token', 'order__id')
    
    def get_queryset(self, request):
        """Optimizar queries con select_related"""
        # ✅ CORRECCIÓN: Excluir gateway_response para evitar errores de deserialización
        # cuando hay datos corruptos (dict en lugar de JSON string)
        qs = super().get_queryset(request)
        return qs.select_related('order').defer('gateway_response')
    
    def order(self, obj):
        return f"Orden #{obj.order.id}"
    order.short_description = 'Pedido'
    order.admin_order_field = 'order__id'
    
    def payment_method(self, obj):
        return obj.get_payment_method_display()
    payment_method.short_description = 'Método'
    payment_method.admin_order_field = 'payment_method'
    
    def status(self, obj):
        return obj.get_status_display()
    status.short_description = 'Estado'
    status.admin_order_field = 'status'
    
    def amount_display(self, obj):
        return f"${obj.amount:,.0f}".replace(',', '.')
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'
    
    def card_info(self, obj):
        """Mostrar información de tarjeta de forma segura"""
        if obj.card_last_four:
            brand = f" ({obj.card_brand})" if obj.card_brand else ""
            return f"**** {obj.card_last_four}{brand}"
        return '-'
    card_info.short_description = 'Tarjeta'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    
    def name(self, obj):
        return obj.name
    name.short_description = 'Nombre'
    name.admin_order_field = 'name'
    
    def code(self, obj):
        return obj.code
    code.short_description = 'Código'
    code.admin_order_field = 'code'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.short_description = 'Activo'
    is_active.boolean = True
    is_active.admin_order_field = 'is_active'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(ShippingCarrier)
class ShippingCarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'has_tracking', 'sort_order', 'created_at')
    list_filter = ('is_active', 'has_tracking', 'api_enabled', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Configuración', {
            'fields': ('requires_address', 'has_tracking', 'api_enabled', 'sort_order')
        }),
        ('Estimaciones', {
            'fields': ('estimated_days_min', 'estimated_days_max')
        }),
        ('Metadatos', {
            'fields': ('logo', 'website')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def name(self, obj):
        return obj.name
    name.short_description = 'Nombre'
    name.admin_order_field = 'name'
    
    def code(self, obj):
        return obj.code
    code.short_description = 'Código'
    code.admin_order_field = 'code'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.short_description = 'Activo'
    is_active.boolean = True
    is_active.admin_order_field = 'is_active'
    
    def has_tracking(self, obj):
        return obj.has_tracking
    has_tracking.short_description = 'Tracking'
    has_tracking.boolean = True
    has_tracking.admin_order_field = 'has_tracking'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(ShippingRule)
class ShippingRuleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'carrier', 'zone', 'priority', 'base_cost', 'cost_per_kg', 'free_shipping_threshold', 'is_active')
    list_filter = ('carrier', 'zone', 'is_active', 'priority', 'created_at')
    search_fields = ('carrier__name', 'zone__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información General', {
            'fields': ('carrier', 'zone', 'priority', 'is_active')
        }),
        ('Criterios de Aplicación', {
            'fields': ('min_weight', 'max_weight', 'min_order_amount'),
            'description': 'La regla aplica si el pedido cumple con estos criterios'
        }),
        ('Costo de Envío', {
            'fields': ('base_cost', 'cost_per_kg', 'free_shipping_threshold')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('carrier', 'zone')
    
    def carrier(self, obj):
        return obj.carrier.name if obj.carrier else '-'
    carrier.short_description = 'Transportista'
    carrier.admin_order_field = 'carrier__name'
    
    def zone(self, obj):
        return obj.zone.name if obj.zone else 'Todas'
    zone.short_description = 'Zona'
    zone.admin_order_field = 'zone__name'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.short_description = 'Activa'
    is_active.boolean = True
    is_active.admin_order_field = 'is_active'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(OrderShippingSnapshot)
class OrderShippingSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'shipping_city', 'shipping_region', 'original_user', 'created_at')
    list_filter = ('shipping_region', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'shipping_city', 'shipping_street')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        """Optimizar queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('original_user', 'original_address')


@admin.register(OrderItemSnapshot)
class OrderItemSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_name', 'product_sku', 'unit_price', 'total_price', 'product_id', 'created_at')
    list_filter = ('created_at', 'product_category_name')
    search_fields = ('product_name', 'product_sku', 'product_brand')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        """Optimizar queries"""
        qs = super().get_queryset(request)
        return qs.select_related()
    
    def unit_price(self, obj):
        return f"${obj.unit_price:,.0f}".replace(',', '.')
    unit_price.short_description = 'Precio unitario'
    unit_price.admin_order_field = 'unit_price'
    
    def total_price(self, obj):
        return f"${obj.total_price:,.0f}".replace(',', '.')
    total_price.short_description = 'Precio total'
    total_price.admin_order_field = 'total_price'

