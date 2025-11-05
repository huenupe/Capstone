from django.contrib import admin
from .models import (
    Order, OrderItem, OrderStatus, OrderStatusHistory,
    Payment, PaymentTransaction, PaymentStatus,
    ShippingZone, ShippingRule
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
    list_display = ('id', 'customer_email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_email', 'customer_name', 'id')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def customer_email(self, obj):
        return obj.customer_email
    customer_email.short_description = 'Correo electrónico'
    customer_email.admin_order_field = 'customer_email'
    
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
    list_display = ('id', 'order', 'status', 'amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__customer_email',)
    
    def status(self, obj):
        return obj.status.code if obj.status else '-'
    status.short_description = 'Estado'
    status.admin_order_field = 'status__code'
    
    def amount(self, obj):
        return f"${obj.amount:,.0f}".replace(',', '.')
    amount.short_description = 'Monto'
    amount.admin_order_field = 'amount'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('buy_order', 'payment', 'status', 'amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buy_order', 'tbk_token')
    
    def buy_order(self, obj):
        return obj.buy_order
    buy_order.short_description = 'Orden de compra'
    buy_order.admin_order_field = 'buy_order'
    
    def status(self, obj):
        return obj.status or '-'
    status.short_description = 'Estado'
    status.admin_order_field = 'status'
    
    def amount(self, obj):
        return f"${obj.amount:,.0f}".replace(',', '.')
    amount.short_description = 'Monto'
    amount.admin_order_field = 'amount'
    
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


@admin.register(ShippingRule)
class ShippingRuleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'rule_type', 'zone', 'priority', 'base_cost', 'free_shipping_threshold', 'is_active')
    list_filter = ('rule_type', 'zone', 'is_active', 'priority')
    search_fields = ('product__name', 'category__name', 'zone__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información General', {
            'fields': ('rule_type', 'zone', 'priority', 'is_active')
        }),
        ('Condiciones', {
            'fields': ('product', 'category'),
            'description': 'Especifique producto O categoría según el tipo de regla'
        }),
        ('Costo de Envío', {
            'fields': ('base_cost', 'free_shipping_threshold')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

