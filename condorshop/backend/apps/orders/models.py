from django.db import models
from django.conf import settings
from apps.products.models import Product


class OrderStatus(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    code = models.CharField(max_length=50, unique=True, db_column='code')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='description')

    class Meta:
        db_table = 'order_statuses'
        verbose_name_plural = 'Order Statuses'

    def __str__(self):
        return self.code


class Order(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='orders'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='orders'
    )
    customer_name = models.CharField(max_length=200, db_column='customer_name')
    customer_email = models.EmailField(max_length=255, db_column='customer_email')
    customer_phone = models.CharField(max_length=50, null=True, blank=True, db_column='customer_phone')
    shipping_street = models.CharField(max_length=200, db_column='shipping_street')
    shipping_city = models.CharField(max_length=100, db_column='shipping_city')
    shipping_region = models.CharField(max_length=100, db_column='shipping_region')
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True, db_column='shipping_postal_code')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_amount')
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        db_column='shipping_cost'
    )
    currency = models.CharField(max_length=10, default='CLP', db_column='currency')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['user'], name='idx_orders_user'),
            models.Index(fields=['status'], name='idx_orders_status'),
            models.Index(fields=['created_at'], name='idx_orders_created'),
            models.Index(fields=['user', 'created_at'], name='idx_orders_user_created'),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.customer_email}"


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.RESTRICT,
        db_column='product_id',
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(db_column='quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='unit_price')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_price')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Order {self.order.id}"


class OrderStatusHistory(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='status_history'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='history_entries'
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_column='changed_at')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='changed_by',
        related_name='status_changes'
    )
    note = models.CharField(max_length=255, null=True, blank=True, db_column='note')

    class Meta:
        db_table = 'order_status_history'
        verbose_name_plural = 'Order Status History'
        ordering = ['-changed_at']

    def __str__(self):
        return f"Order {self.order.id} - {self.status.code} at {self.changed_at}"


class PaymentStatus(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    code = models.CharField(max_length=50, unique=True, db_column='code')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='description')

    class Meta:
        db_table = 'payment_statuses'
        verbose_name_plural = 'Payment Statuses'

    def __str__(self):
        return self.code


class Payment(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='payments'
    )
    payment_method = models.CharField(max_length=50, default='webpay', db_column='payment_method')
    status = models.ForeignKey(
        PaymentStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='amount')
    currency = models.CharField(max_length=10, default='CLP', db_column='currency')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment {self.id} - Order {self.order.id} - {self.status.code}"


class PaymentTransaction(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        db_column='payment_id',
        related_name='transactions'
    )
    tbk_token = models.CharField(max_length=200, unique=True, db_column='tbk_token')
    buy_order = models.CharField(max_length=64, unique=True, db_column='buy_order')
    session_id = models.CharField(max_length=64, db_column='session_id')
    authorization_code = models.CharField(max_length=64, null=True, blank=True, db_column='authorization_code')
    response_code = models.IntegerField(null=True, blank=True, db_column='response_code')
    card_detail = models.CharField(max_length=100, null=True, blank=True, db_column='card_detail')
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='amount')
    status = models.CharField(max_length=50, null=True, blank=True, db_column='status')
    processed_at = models.DateTimeField(null=True, blank=True, db_column='processed_at')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'payment_transactions'
        indexes = [
            models.Index(fields=['tbk_token'], name='idx_token'),
            models.Index(fields=['buy_order'], name='idx_buy_order'),
        ]

    def __str__(self):
        return f"Transaction {self.buy_order} - {self.status}"

