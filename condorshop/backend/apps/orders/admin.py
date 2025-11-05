from django.contrib import admin
from .models import Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentTransaction, PaymentStatus


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')


@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'total_price')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
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

