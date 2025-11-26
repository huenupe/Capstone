from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
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
    # NUEVO: Relación con snapshot
    shipping_snapshot = models.OneToOneField(
        'OrderShippingSnapshot',
        on_delete=models.PROTECT,  # NUNCA eliminar snapshots
        related_name='order',
        null=True,  # Temporal para migración (se hará obligatorio después)
        blank=True,
        db_column='shipping_snapshot_id',
        verbose_name='Snapshot de envío'
    )
    # NOTA: Los campos customer_name, customer_email, customer_phone, shipping_street, 
    # shipping_city, shipping_region, shipping_postal_code fueron eliminados.
    # Ahora se obtienen desde shipping_snapshot.
    total_amount = models.PositiveIntegerField(db_column='total_amount', verbose_name='Monto total')
    shipping_cost = models.PositiveIntegerField(
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
            models.Index(fields=['status', 'created_at'], name='idx_orders_status_created'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gt=0),
                name='order_total_amount_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(shipping_cost__gte=0),
                name='order_shipping_cost_non_negative'
            ),
        ]

    def __str__(self):
        email = self.shipping_snapshot.customer_email if self.shipping_snapshot else 'Sin snapshot'
        return f"Pedido {self.id} - {email}"


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
    # NUEVO: Relación con snapshot de precios
    price_snapshot = models.OneToOneField(
        'OrderItemSnapshot',
        on_delete=models.PROTECT,  # NUNCA eliminar snapshots
        related_name='order_item',
        null=True,  # Temporal para migración (se hará obligatorio después)
        blank=True,
        db_column='price_snapshot_id',
        verbose_name='Snapshot de precio'
    )
    quantity = models.PositiveIntegerField(db_column='quantity', verbose_name='Cantidad')
    # NOTA: unit_price y total_price se mantienen para compatibilidad y consultas rápidas
    # pero los valores históricos se obtienen desde price_snapshot
    unit_price = models.PositiveIntegerField(db_column='unit_price', verbose_name='Precio unitario')
    total_price = models.PositiveIntegerField(db_column='total_price', verbose_name='Precio total')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='order_item_quantity_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name='order_item_unit_price_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gt=0),
                name='order_item_total_price_positive'
            ),
        ]

    def __str__(self):
        product_name = self.price_snapshot.product_name if self.price_snapshot else (self.product.name if self.product else 'Producto eliminado')
        return f"{self.quantity}x {product_name} - Pedido {self.order.id}"


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


class OrderShippingSnapshot(models.Model):
    """
    Snapshot inmutable de información de envío.
    Preserva datos históricos independiente de cambios en User/Address.
    """
    id = models.BigAutoField(primary_key=True, db_column='id')
    
    # Datos del cliente al momento de la orden
    customer_name = models.CharField(max_length=255, db_column='customer_name', verbose_name='Nombre del cliente')
    customer_email = models.EmailField(max_length=255, db_column='customer_email', verbose_name='Correo del cliente')
    customer_phone = models.CharField(max_length=20, blank=True, db_column='customer_phone', verbose_name='Teléfono del cliente')
    
    # Dirección de envío completa
    shipping_street = models.CharField(max_length=255, db_column='shipping_street', verbose_name='Calle de envío')
    shipping_city = models.CharField(max_length=100, db_column='shipping_city', verbose_name='Ciudad de envío')
    shipping_region = models.CharField(max_length=100, db_column='shipping_region', verbose_name='Región de envío')
    shipping_postal_code = models.CharField(max_length=20, blank=True, db_column='shipping_postal_code', verbose_name='Código postal')
    shipping_country = models.CharField(max_length=100, default='Chile', db_column='shipping_country', verbose_name='País')
    
    # Referencias para trazabilidad (nullable si se eliminan)
    original_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='original_user_id',
        related_name='shipping_snapshots',
        verbose_name='Usuario original'
    )
    original_address = models.ForeignKey(
        'users.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='original_address_id',
        related_name='order_snapshots',
        verbose_name='Dirección original'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    
    class Meta:
        db_table = 'order_shipping_snapshots'
        verbose_name = 'Snapshot de Envío'
        verbose_name_plural = 'Snapshots de Envío'
        indexes = [
            models.Index(fields=['created_at'], name='idx_snapshot_created'),
            models.Index(fields=['original_user'], name='idx_snapshot_user'),
        ]
    
    def __str__(self):
        return f"Snapshot: {self.customer_name} - {self.shipping_city}"


class OrderItemSnapshot(models.Model):
    """
    Snapshot inmutable de información de precio y producto.
    Preserva datos históricos independiente de cambios en Product.
    """
    id = models.BigAutoField(primary_key=True, db_column='id')
    
    # Información del producto al momento de la orden
    product_name = models.CharField(max_length=200, db_column='product_name', verbose_name='Nombre del producto')
    product_sku = models.CharField(max_length=64, db_column='product_sku', verbose_name='SKU del producto')
    product_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='product_id',
        verbose_name='ID del producto original',
        help_text='Referencia al producto original (nullable si se elimina)'
    )
    
    # Precios al momento de la orden (en CLP enteros)
    unit_price = models.PositiveIntegerField(db_column='unit_price', verbose_name='Precio unitario')
    total_price = models.PositiveIntegerField(db_column='total_price', verbose_name='Precio total')
    
    # Información adicional del producto (opcional, para trazabilidad)
    product_brand = models.CharField(max_length=100, null=True, blank=True, db_column='product_brand', verbose_name='Marca')
    product_category_name = models.CharField(max_length=200, null=True, blank=True, db_column='product_category_name', verbose_name='Categoría')
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    
    class Meta:
        db_table = 'order_item_snapshots'
        verbose_name = 'Snapshot de Item de Pedido'
        verbose_name_plural = 'Snapshots de Items de Pedido'
        indexes = [
            models.Index(fields=['created_at'], name='idx_item_snapshot_created'),
            models.Index(fields=['product_id'], name='idx_item_snapshot_product'),
            models.Index(fields=['product_sku'], name='idx_item_snapshot_sku'),
        ]
    
    def __str__(self):
        return f"Snapshot: {self.product_name} - ${self.unit_price:,} CLP"


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
    """
    Registro principal del pago asociado a un pedido.
    Un Payment puede tener múltiples PaymentTransaction (intentos de pago).
    El monto y estado final se obtienen de la transacción exitosa.
    """
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
        verbose_name='Estado',
        help_text='Estado del pago (sincronizado con la transacción actual)'
    )
    # REMOVIDO: amount - ahora se obtiene de la transacción exitosa
    currency = models.CharField(max_length=10, default='CLP', db_column='currency', verbose_name='Moneda')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'payments'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        indexes = [
            models.Index(fields=['order'], name='idx_payment_order'),
            models.Index(fields=['status'], name='idx_payment_status'),
        ]

    def __str__(self):
        return f"Pago {self.id} - Pedido {self.order.id} - {self.status.code}"
    
    @property
    def amount(self):
        """
        Obtener monto desde la transacción exitosa o la más reciente.
        Retorna None si no hay transacciones.
        NOTA: PaymentTransaction ahora se relaciona con Order, no con Payment.
        Accedemos a través de order.payment_transactions.
        """
        # Buscar transacción exitosa primero (a través de Order)
        successful_tx = self.order.payment_transactions.filter(status='approved').first()
        if successful_tx:
            return successful_tx.amount
        
        # Si no hay exitosa, retornar la más reciente
        latest_tx = self.order.payment_transactions.order_by('-created_at').first()
        return latest_tx.amount if latest_tx else None
    
    @property
    def current_transaction(self):
        """
        Obtener la transacción actual (exitosa o la más reciente).
        NOTA: PaymentTransaction ahora se relaciona con Order, no con Payment.
        Accedemos a través de order.payment_transactions.
        """
        successful_tx = self.order.payment_transactions.filter(status='approved').first()
        if successful_tx:
            return successful_tx
        return self.order.payment_transactions.order_by('-created_at').first()
    
    def get_amount(self):
        """
        Método helper para obtener monto (compatibilidad con código existente).
        """
        return self.amount


class PaymentTransaction(models.Model):
    """
    Transacción de pago - Compatible con Webpay (Transbank)
    
    IMPORTANTE: Este modelo NUNCA debe almacenar:
    - Números completos de tarjetas
    - CVV/CVC
    - Datos sensibles de tarjetas
    """
    
    PAYMENT_METHOD_CHOICES = [
        ('webpay', 'Webpay (Tarjeta)'),
        ('transfer', 'Transferencia Bancaria'),
        ('cash', 'Efectivo (Retiro en tienda)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Relación con orden (cambiada de Payment a Order según plan)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='payment_transactions',
        verbose_name='Pedido'
    )
    
    # Información del pago
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='webpay',
        db_column='payment_method',
        verbose_name='Método de pago'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_column='status',
        verbose_name='Estado'
    )
    amount = models.PositiveIntegerField(db_column='amount', verbose_name='Monto')
    currency = models.CharField(max_length=3, default='CLP', db_column='currency', verbose_name='Moneda')
    
    # Datos específicos de Webpay (solo cuando payment_method='webpay')
    webpay_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_column='webpay_token',
        verbose_name='Token Webpay'
    )
    webpay_buy_order = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column='webpay_buy_order',
        verbose_name='Orden de compra Webpay'
    )
    webpay_authorization_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_column='webpay_authorization_code',
        verbose_name='Código de autorización'
    )
    webpay_transaction_date = models.DateTimeField(
        blank=True,
        null=True,
        db_column='webpay_transaction_date',
        verbose_name='Fecha de transacción'
    )
    
    # Datos de tarjeta (SOLO últimos 4 dígitos y tipo - seguro)
    card_last_four = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        db_column='card_last_four',
        verbose_name='Últimos 4 dígitos'
    )
    card_brand = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_column='card_brand',
        verbose_name='Marca de tarjeta',
        help_text='visa, mastercard, etc'
    )
    
    # Respuesta completa del gateway (JSON para debugging)
    gateway_response = models.JSONField(
        blank=True,
        null=True,
        db_column='gateway_response',
        verbose_name='Respuesta del gateway'
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transacción de Pago'
        verbose_name_plural = 'Transacciones de Pago'
        indexes = [
            models.Index(fields=['order'], name='idx_payment_tx_order'),
            models.Index(fields=['status'], name='idx_payment_tx_status'),
            models.Index(fields=['webpay_token'], name='idx_payment_webpay_token'),
            models.Index(fields=['created_at'], name='idx_payment_tx_created'),
        ]
        constraints = [
            # Constraint único en webpay_buy_order para prevenir duplicados (Error 21)
            # Solo aplica cuando webpay_buy_order no es NULL
            models.UniqueConstraint(
                fields=['webpay_buy_order'],
                condition=models.Q(webpay_buy_order__isnull=False),
                name='idx_payment_buy_order_unique'
            ),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.payment_method} - {self.status}"
    
    @property
    def is_approved(self):
        """Indica si la transacción está aprobada"""
        return self.status == 'approved'
    
    def mark_as_approved(self, webpay_data=None):
        """
        Marca pago como aprobado y guarda datos de Webpay
        
        Args:
            webpay_data (dict): Diccionario con datos de Webpay:
                - authorization_code
                - transaction_date
                - card_last_four
                - card_brand
                - gateway_response (opcional, respuesta completa)
        """
        self.status = 'approved'
        if webpay_data:
            self.webpay_authorization_code = webpay_data.get('authorization_code')
            self.webpay_transaction_date = webpay_data.get('transaction_date')
            self.card_last_four = webpay_data.get('card_last_four')
            self.card_brand = webpay_data.get('card_brand')
            if 'gateway_response' in webpay_data:
                self.gateway_response = webpay_data.get('gateway_response')
        self.save()


class ShippingZone(models.Model):
    """Zona de envío (región geográfica)"""
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(
        max_length=120,
        unique=True,
        db_column='name',
        verbose_name='Nombre de la zona',
        help_text='Etiqueta visible en el panel para identificar la zona de envío.'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        db_column='code',
        verbose_name='Código',
        help_text='Código único de la zona (ej: REGION_METROPOLITANA)'
    )
    regions = models.JSONField(
        default=list,
        db_column='regions',
        verbose_name='Regiones',
        help_text='Lista de regiones incluidas en esta zona (ej: ["Región Metropolitana", "Santiago"])'
    )
    is_active = models.BooleanField(
        default=True,
        db_column='is_active',
        verbose_name='Activa'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

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


class ShippingCarrier(models.Model):
    """
    Carriers/transportistas disponibles.
    Ej: Chilexpress, Correos de Chile, Starken, Retiro en tienda
    """
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, db_column='name', verbose_name='Nombre')
    code = models.CharField(max_length=50, unique=True, db_column='code', verbose_name='Código')
    description = models.TextField(blank=True, db_column='description', verbose_name='Descripción')
    
    # Configuración
    is_active = models.BooleanField(default=True, db_column='is_active', verbose_name='Activo')
    requires_address = models.BooleanField(default=True, db_column='requires_address', verbose_name='Requiere dirección')
    has_tracking = models.BooleanField(default=False, db_column='has_tracking', verbose_name='Soporta tracking')
    api_enabled = models.BooleanField(default=False, db_column='api_enabled', verbose_name='API habilitada')
    
    # Estimaciones
    estimated_days_min = models.IntegerField(default=1, db_column='estimated_days_min', verbose_name='Días mínimos')
    estimated_days_max = models.IntegerField(default=3, db_column='estimated_days_max', verbose_name='Días máximos')
    
    # Metadatos
    logo = models.ImageField(upload_to='carriers/', blank=True, null=True, db_column='logo', verbose_name='Logo')
    website = models.URLField(blank=True, db_column='website', verbose_name='Sitio web')
    sort_order = models.IntegerField(default=0, db_column='sort_order', verbose_name='Orden')
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')
    
    class Meta:
        db_table = 'shipping_carriers'
        ordering = ['sort_order', 'name']
        verbose_name = 'Transportista'
        verbose_name_plural = 'Transportistas'
    
    def __str__(self):
        return self.name


class ShippingRule(models.Model):
    """
    Reglas de cálculo de costos de envío.
    Soporta múltiples criterios: zona, peso, monto mínimo.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    carrier = models.ForeignKey(
        'ShippingCarrier',
        on_delete=models.CASCADE,
        db_column='carrier_id',
        related_name='rules',
        verbose_name='Transportista'
    )
    zone = models.ForeignKey(
        'ShippingZone',
        on_delete=models.CASCADE,
        db_column='zone_id',
        related_name='rules',
        null=True,
        blank=True,
        help_text="Zona geográfica. NULL = aplica a todas las zonas",
        verbose_name='Zona de envío'
    )
    
    # Criterios de aplicación
    min_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        db_column='min_weight',
        help_text="Peso mínimo en kg",
        verbose_name='Peso mínimo (kg)'
    )
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='max_weight',
        help_text="Peso máximo en kg. NULL = sin límite",
        verbose_name='Peso máximo (kg)'
    )
    min_order_amount = models.PositiveIntegerField(
        default=0,
        db_column='min_order_amount',
        help_text="Monto mínimo de orden en pesos",
        verbose_name='Monto mínimo'
    )
    
    # Costos
    base_cost = models.PositiveIntegerField(
        db_column='base_cost',
        help_text="Costo base del envío",
        verbose_name='Costo base'
    )
    cost_per_kg = models.PositiveIntegerField(
        default=0,
        db_column='cost_per_kg',
        help_text="Costo adicional por kg",
        verbose_name='Costo por kg'
    )
    
    # Envío gratis
    free_shipping_threshold = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='free_shipping_threshold',
        help_text="Monto para envío gratis. NULL = no aplica",
        verbose_name='Umbral de envío gratis'
    )
    
    # Configuración
    is_active = models.BooleanField(default=True, db_column='is_active', verbose_name='Activa')
    priority = models.IntegerField(
        default=0,
        db_column='priority',
        help_text="Prioridad al evaluar múltiples reglas (mayor = más prioritario)",
        verbose_name='Prioridad'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'shipping_rules'
        ordering = ['-priority', 'base_cost']
        verbose_name = 'Regla de Envío'
        verbose_name_plural = 'Reglas de Envío'
        indexes = [
            models.Index(fields=['carrier', 'zone', 'is_active'], name='idx_rule_carrier_zone'),
            models.Index(fields=['-priority'], name='idx_rule_priority'),
        ]
    
    def __str__(self):
        zone_str = f" - {self.zone}" if self.zone else " (todas las zonas)"
        return f"{self.carrier}{zone_str}: ${self.base_cost}"
    
    def calculate_cost(self, order_amount, total_weight):
        """
        Calcula el costo de envío según esta regla.
        
        Args:
            order_amount: Monto total de la orden en pesos
            total_weight: Peso total en kg
        
        Returns:
            int: Costo de envío (0 si aplica envío gratis)
        """
        # Verificar si aplica envío gratis
        if self.free_shipping_threshold and order_amount >= self.free_shipping_threshold:
            return 0
        
        # Costo base + costo por peso
        cost = self.base_cost
        if self.cost_per_kg > 0 and total_weight > 0:
            cost += int(self.cost_per_kg * float(total_weight))
        
        return cost
    
    def applies_to(self, zone, order_amount, total_weight):
        """
        Verifica si esta regla aplica a los parámetros dados.
        
        Returns:
            bool: True si la regla es aplicable
        """
        if not self.is_active:
            return False
        
        # Verificar zona
        if self.zone and self.zone != zone:
            return False
        
        # Verificar peso
        if float(total_weight) < float(self.min_weight):
            return False
        if self.max_weight and float(total_weight) > float(self.max_weight):
            return False
        
        # Verificar monto mínimo
        if order_amount < self.min_order_amount:
            return False
        
        return True

