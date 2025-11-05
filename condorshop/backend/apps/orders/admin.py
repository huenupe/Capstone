from django.contrib import admin
from .models import (
    Order, OrderItem, OrderStatus, OrderStatusHistory,
    Payment, PaymentTransaction, PaymentStatus,
    ShippingZone, ShippingRule
)


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')


@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__customer_email',)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('buy_order', 'payment', 'status', 'amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buy_order', 'tbk_token')


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')


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

