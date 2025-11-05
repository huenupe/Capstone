from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.products.models import Product, Category


class OrderStatus(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    code = models.CharField(max_length=50, unique=True, db_column='code', verbose_name='Código')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='description', verbose_name='Descripción')

    class Meta:
        db_table = 'order_statuses'
        verbose_name = 'Estado de Pedido'
        verbose_name_plural = 'Estados de Pedido'

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
        related_name='orders',
        verbose_name='Usuario'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='orders',
        verbose_name='Estado'
    )
    customer_name = models.CharField(max_length=200, db_column='customer_name', verbose_name='Nombre del cliente')
    customer_email = models.EmailField(max_length=255, db_column='customer_email', verbose_name='Correo del cliente')
    customer_phone = models.CharField(max_length=50, null=True, blank=True, db_column='customer_phone', verbose_name='Teléfono del cliente')
    shipping_street = models.CharField(max_length=200, db_column='shipping_street', verbose_name='Calle de envío')
    shipping_city = models.CharField(max_length=100, db_column='shipping_city', verbose_name='Ciudad de envío')
    shipping_region = models.CharField(max_length=100, db_column='shipping_region', verbose_name='Región de envío')
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True, db_column='shipping_postal_code', verbose_name='Código postal de envío')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_amount', verbose_name='Monto total')
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        db_column='shipping_cost',
        verbose_name='Costo de envío'
    )
    currency = models.CharField(max_length=10, default='CLP', db_column='currency', verbose_name='Moneda')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'orders'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        indexes = [
            models.Index(fields=['user'], name='idx_orders_user'),
            models.Index(fields=['status'], name='idx_orders_status'),
            models.Index(fields=['created_at'], name='idx_orders_created'),
            models.Index(fields=['user', 'created_at'], name='idx_orders_user_created'),
        ]

    def __str__(self):
        return f"Pedido {self.id} - {self.customer_email}"


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.RESTRICT,
        db_column='product_id',
        related_name='order_items',
        verbose_name='Producto'
    )
    quantity = models.PositiveIntegerField(db_column='quantity', verbose_name='Cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='unit_price', verbose_name='Precio unitario')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_price', verbose_name='Precio total')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'

    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Pedido {self.order.id}"


class OrderStatusHistory(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='status_history',
        verbose_name='Pedido'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='history_entries',
        verbose_name='Estado'
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_column='changed_at', verbose_name='Cambiado el')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='changed_by',
        related_name='status_changes',
        verbose_name='Cambiado por'
    )
    note = models.CharField(max_length=255, null=True, blank=True, db_column='note', verbose_name='Nota')

    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Historial de Estado de Pedido'
        verbose_name_plural = 'Historial de Estados de Pedido'
        ordering = ['-changed_at']

    def __str__(self):
        return f"Pedido {self.order.id} - {self.status.code} en {self.changed_at}"


class PaymentStatus(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    code = models.CharField(max_length=50, unique=True, db_column='code', verbose_name='Código')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='description', verbose_name='Descripción')

    class Meta:
        db_table = 'payment_statuses'
        verbose_name = 'Estado de Pago'
        verbose_name_plural = 'Estados de Pago'

    def __str__(self):
        return self.code


class Payment(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='payments',
        verbose_name='Pedido'
    )
    payment_method = models.CharField(max_length=50, default='webpay', db_column='payment_method', verbose_name='Método de pago')
    status = models.ForeignKey(
        PaymentStatus,
        on_delete=models.RESTRICT,
        db_column='status_id',
        related_name='payments',
        verbose_name='Estado'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='amount', verbose_name='Monto')
    currency = models.CharField(max_length=10, default='CLP', db_column='currency', verbose_name='Moneda')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'payments'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - Pedido {self.order.id} - {self.status.code}"


class PaymentTransaction(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        db_column='payment_id',
        related_name='transactions',
        verbose_name='Pago'
    )
    tbk_token = models.CharField(max_length=200, unique=True, db_column='tbk_token', verbose_name='Token TBK')
    buy_order = models.CharField(max_length=64, unique=True, db_column='buy_order', verbose_name='Orden de compra')
    session_id = models.CharField(max_length=64, db_column='session_id', verbose_name='ID de sesión')
    authorization_code = models.CharField(max_length=64, null=True, blank=True, db_column='authorization_code', verbose_name='Código de autorización')
    response_code = models.IntegerField(null=True, blank=True, db_column='response_code', verbose_name='Código de respuesta')
    card_detail = models.CharField(max_length=100, null=True, blank=True, db_column='card_detail', verbose_name='Detalle de tarjeta')
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='amount', verbose_name='Monto')
    status = models.CharField(max_length=50, null=True, blank=True, db_column='status', verbose_name='Estado')
    processed_at = models.DateTimeField(null=True, blank=True, db_column='processed_at', verbose_name='Procesado el')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transacción de Pago'
        verbose_name_plural = 'Transacciones de Pago'
        indexes = [
            models.Index(fields=['tbk_token'], name='idx_token'),
            models.Index(fields=['buy_order'], name='idx_buy_order'),
        ]

    def __str__(self):
        return f"Transacción {self.buy_order} - {self.status}"


class ShippingZone(models.Model):
    """Zona de envío (región geográfica)"""
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, unique=True, db_column='name')
    code = models.CharField(max_length=50, unique=True, db_column='code', help_text='Código único de la zona (ej: REGION_METROPOLITANA)')
    regions = models.JSONField(
        default=list,
        db_column='regions',
        help_text='Lista de regiones incluidas en esta zona (ej: ["Región Metropolitana", "Santiago"])'
    )
    is_active = models.BooleanField(default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'shipping_zones'
        verbose_name = 'Zona de Envío'
        verbose_name_plural = 'Zonas de Envío'
        indexes = [
            models.Index(fields=['code'], name='idx_zone_code'),
            models.Index(fields=['is_active'], name='idx_zone_active'),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ShippingRule(models.Model):
    """Regla de envío con prioridad y condiciones"""
    RULE_TYPE_CHOICES = [
        ('PRODUCT', 'Producto específico'),
        ('CATEGORY', 'Categoría'),
        ('ALL', 'Todas las ventas'),
    ]

    id = models.AutoField(primary_key=True, db_column='id')
    zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.CASCADE,
        db_column='zone_id',
        related_name='shipping_rules',
        null=True,
        blank=True,
        help_text='Si es null, aplica a todas las zonas'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        db_column='rule_type',
        help_text='Tipo de regla: PRODUCT (producto), CATEGORY (categoría), ALL (todas)'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='shipping_rules',
        null=True,
        blank=True,
        help_text='Producto específico (solo si rule_type=PRODUCT)'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_column='category_id',
        related_name='shipping_rules',
        null=True,
        blank=True,
        help_text='Categoría específica (solo si rule_type=CATEGORY)'
    )
    priority = models.IntegerField(
        default=0,
        db_column='priority',
        validators=[MinValueValidator(0)],
        help_text='Prioridad (mayor número = mayor prioridad). Las reglas de PRODUCT tienen prioridad sobre CATEGORY, y CATEGORY sobre ALL.'
    )
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        db_column='base_cost',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Costo base de envío'
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='free_shipping_threshold',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Umbral para envío gratis (null = no hay envío gratis para esta regla)'
    )
    is_active = models.BooleanField(default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'shipping_rules'
        verbose_name = 'Regla de Envío'
        verbose_name_plural = 'Reglas de Envío'
        indexes = [
            models.Index(fields=['zone', 'is_active'], name='idx_rule_zone_active'),
            models.Index(fields=['rule_type', 'is_active'], name='idx_rule_type_active'),
            models.Index(fields=['priority'], name='idx_rule_priority'),
        ]
        ordering = ['-priority', '-created_at']

    def __str__(self):
        if self.rule_type == 'PRODUCT' and self.product:
            return f"Envío {self.product.name} - {self.zone.name if self.zone else 'Todas'}"
        elif self.rule_type == 'CATEGORY' and self.category:
            return f"Envío {self.category.name} - {self.zone.name if self.zone else 'Todas'}"
        else:
            return f"Envío General - {self.zone.name if self.zone else 'Todas'}"

    def clean(self):
        """Validar que los campos específicos correspondan al tipo de regla"""
        from django.core.exceptions import ValidationError
        if self.rule_type == 'PRODUCT' and not self.product:
            raise ValidationError('Debe especificar un producto cuando rule_type es PRODUCT')
        if self.rule_type == 'CATEGORY' and not self.category:
            raise ValidationError('Debe especificar una categoría cuando rule_type es CATEGORY')
        if self.rule_type == 'ALL' and (self.product or self.category):
            raise ValidationError('No debe especificar producto o categoría cuando rule_type es ALL')

