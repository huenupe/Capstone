from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from apps.common.utils import format_clp


class Category(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, db_column='name', verbose_name='Nombre')
    slug = models.SlugField(max_length=150, unique=True, db_column='slug', verbose_name='URL amigable')
    description = models.TextField(null=True, blank=True, db_column='description', verbose_name='Descripción')
    # NUEVO: Jerarquía de categorías
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='parent_category_id',
        related_name='subcategories',
        verbose_name='Categoría padre',
        help_text='Categoría padre para crear jerarquías (ej: "Electrónica" > "Audio" > "Auriculares")'
    )
    # NUEVO: Campos adicionales para jerarquía completa
    level = models.SmallIntegerField(
        default=0,
        editable=False,
        db_column='level',
        verbose_name='Nivel',
        help_text='Nivel en la jerarquía (0 = raíz, calculado automáticamente)'
    )
    sort_order = models.IntegerField(
        default=0,
        db_column='sort_order',
        verbose_name='Orden',
        help_text='Orden de visualización (menor = primero)'
    )
    active = models.BooleanField(
        default=True,
        db_column='active',
        verbose_name='Activa',
        help_text='Indica si la categoría está activa y visible'
    )
    image = models.ImageField(
        upload_to='categorias/',
        null=True,
        blank=True,
        db_column='image',
        verbose_name='Imagen',
        help_text='Imagen representativa de la categoría. Se recomienda formato cuadrado (por ejemplo 600x600).'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'categories'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug'], name='idx_category_slug'),
            models.Index(fields=['parent_category'], name='idx_category_parent'),
            models.Index(fields=['parent_category', 'active'], name='idx_category_parent_active'),
        ]
        constraints = [
            # Permitir nombres duplicados solo si tienen diferentes padres
            models.UniqueConstraint(
                fields=['name', 'parent_category'],
                name='uq_category_name_parent'
            ),
        ]

    def __str__(self):
        """Mostrar jerarquía completa si tiene padre"""
        if self.parent_category:
            return f"{self.parent_category} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Obtener ruta completa de la categoría (ej: 'Electrónica > Audio > Auriculares')"""
        path = [self.name]
        parent = self.parent_category
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent_category
        return ' > '.join(path)
    
    def get_depth(self):
        """Obtener profundidad en la jerarquía (0 = raíz, 1 = hijo, etc.)"""
        # Usar level si está disponible, sino calcular
        if hasattr(self, 'level') and self.level is not None:
            return self.level
        depth = 0
        parent = self.parent_category
        while parent:
            depth += 1
            parent = parent.parent_category
        return depth
    
    def get_ancestors(self, include_self=False):
        """Retorna lista de ancestros (desde raíz hasta esta categoría)"""
        ancestors = []
        if include_self:
            ancestors.append(self)
        parent = self.parent_category
        while parent:
            ancestors.insert(0, parent)
            parent = parent.parent_category
        return ancestors
    
    def get_descendants(self, include_self=False):
        """Retorna todos los descendientes (recursivo)"""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_root(self):
        """Retorna la categoría raíz de esta jerarquía"""
        if not self.parent_category:
            return self
        return self.parent_category.get_root()
    
    def is_leaf(self):
        """Verifica si es categoría hoja (sin hijos)"""
        return not self.subcategories.filter(active=True).exists()
    
    def is_root(self):
        """Verifica si es categoría raíz"""
        return self.parent_category is None
    
    @classmethod
    def get_roots(cls):
        """Retorna todas las categorías raíz activas"""
        return cls.objects.filter(parent_category__isnull=True, active=True)

    def clean(self):
        """Validar que no haya ciclos en la jerarquía"""
        from django.core.exceptions import ValidationError
        
        if self.parent_category:
            # Verificar que no sea su propio padre
            if self.parent_category == self:
                raise ValidationError({'parent_category': 'Una categoría no puede ser su propio padre.'})
            
            # Verificar que no cree un ciclo (el padre no puede ser descendiente de esta categoría)
            # Solo validar si esta categoría ya tiene ID (está guardada)
            if self.pk:
                current = self.parent_category
                visited = {self.pk}  # Incluir esta categoría para detectar ciclos
                
                while current:
                    if current.pk and current.pk in visited:
                        raise ValidationError({
                            'parent_category': 'No se puede crear un ciclo en la jerarquía. Esta categoría sería ancestro de su propio padre.'
                        })
                    if current.pk:
                        visited.add(current.pk)
                    current = current.parent_category

    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.full_clean()
        
        if not self.slug:
            # Generar slug único considerando la jerarquía
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Calcular level automáticamente basado en parent
        if self.parent_category:
            self.level = self.parent_category.level + 1
            # Validar profundidad máxima
            if self.level > 3:
                raise ValueError("Máximo 3 niveles de jerarquía permitidos")
        else:
            self.level = 0
        
        super().save(*args, **kwargs)


class Product(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='category_id',
        related_name='products',
        verbose_name='Categoría'
    )
    name = models.CharField(max_length=200, db_column='name', verbose_name='Nombre')
    slug = models.SlugField(max_length=200, unique=True, db_column='slug', verbose_name='URL amigable')
    description = models.TextField(null=True, blank=True, db_column='description', verbose_name='Descripción')
    price = models.PositiveIntegerField(db_column='price', verbose_name='Precio')
    discount_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='discount_price',
        help_text='Precio final después del descuento en pesos chilenos (CLP, sin decimales). Si está configurado, se usa este precio directamente. Ejemplo: 22990',
        verbose_name='Precio final del descuento'
    )
    discount_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='discount_amount',
        help_text='Monto fijo a descontar del precio en pesos chilenos (CLP, sin decimales). Ejemplo: si el precio es $100000 y aquí pones $20000, el precio final será $80000.',
        verbose_name='Monto a descontar'
    )
    discount_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_column='discount_percent',
        help_text='Porcentaje de descuento. Ingresa un número entero entre 0 y 100 (ej: 20 para 20%).',
        verbose_name='Descuento por porcentaje (%)'
    )
    # INVENTARIO
    stock_qty = models.PositiveIntegerField(default=0, db_column='stock_qty', verbose_name='Cantidad en stock')
    stock_reserved = models.PositiveIntegerField(
        default=0,
        db_column='stock_reserved',
        verbose_name='Stock reservado',
        help_text='Cantidad de stock reservada para pedidos pendientes'
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        db_column='low_stock_threshold',
        verbose_name='Umbral de stock bajo',
        help_text='Cantidad mínima antes de considerar stock bajo'
    )
    allow_backorder = models.BooleanField(
        default=False,
        db_column='allow_backorder',
        verbose_name='Permitir backorder',
        help_text='Permitir ventas cuando no hay stock disponible'
    )
    # NUEVO: Para cálculo de shipping
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        db_column='weight',
        help_text="Peso del producto en kilogramos",
        verbose_name='Peso (kg)'
    )
    brand = models.CharField(max_length=100, null=True, blank=True, db_column='brand', verbose_name='Marca')
    sku = models.CharField(max_length=64, unique=True, db_column='sku', verbose_name='SKU')
    active = models.BooleanField(default=True, db_column='active', verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'products'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['category'], name='idx_product_category'),
            models.Index(fields=['slug'], name='idx_product_slug'),
            models.Index(fields=['active'], name='idx_product_active'),
            models.Index(fields=['price'], name='idx_product_price'),
            models.Index(fields=['stock_qty'], name='idx_product_stock'),
            models.Index(fields=['created_at'], name='idx_product_created_at'),
            models.Index(fields=['name'], name='idx_product_name'),
            models.Index(fields=['active', '-created_at'], name='idx_product_active_created'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(discount_percent__isnull=True) | Q(discount_percent__gte=0, discount_percent__lte=100),
                name='pct_range_0_100'
            ),
            models.CheckConstraint(
                condition=~(
                    (Q(discount_price__isnull=False) & Q(discount_amount__isnull=False)) |
                    (Q(discount_price__isnull=False) & Q(discount_percent__isnull=False)) |
                    (Q(discount_amount__isnull=False) & Q(discount_percent__isnull=False))
                ),
                name='only_one_discount_mode'
            ),
            models.CheckConstraint(
                condition=Q(stock_qty__gte=0),
                name='product_stock_qty_non_negative'
            ),
            models.CheckConstraint(
                condition=Q(stock_reserved__gte=0),
                name='product_stock_reserved_non_negative'
            ),
            models.CheckConstraint(
                condition=Q(stock_reserved__lte=models.F('stock_qty')),
                name='product_stock_reserved_lte_qty'
            ),
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name='product_price_positive'
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        price_int = int(self.price or 0)

        if self.discount_price is not None:
            if self.discount_price <= 0:
                self.discount_price = None
            elif self.discount_price > price_int:
                raise ValueError('El precio final del descuento no puede ser mayor que el precio original')

        if self.discount_amount is not None:
            if self.discount_amount <= 0:
                self.discount_amount = None
            elif self.discount_amount > price_int:
                raise ValueError('El monto a descontar no puede ser mayor que el precio original')

        if self.discount_percent is not None:
            if not (0 <= self.discount_percent <= 100):
                raise ValueError('El porcentaje de descuento debe estar entre 0 y 100')
            if self.discount_percent == 0:
                self.discount_percent = None

        if self.discount_price is not None:
            self.discount_amount = None
            self.discount_percent = None
        elif self.discount_amount is not None:
            self.discount_percent = None
        
        super().save(*args, **kwargs)
    
    @property
    def final_price(self) -> int:
        """
        Precio final en CLP entero.
        - discount_price: sobrescribe el precio base.
        - discount_amount: resta monto fijo.
        - discount_percent: aplica porcentaje con redondeo half-up entero.
        """
        base = int(self.price or 0)

        if self.discount_price is not None:
            return max(int(self.discount_price), 0)

        if self.discount_amount is not None:
            return max(base - int(self.discount_amount), 0)

        if self.discount_percent is not None:
            pct = int(self.discount_percent)
            discount = (base * pct + 50) // 100
            return max(base - discount, 0)

        return base
    
    @property
    def calculated_discount_percent(self):
        """
        Porcentaje de descuento calculado automáticamente basado en el precio final.
        Retorna un entero (1-100)
        """
        base = int(self.price or 0)
        final_int = int(self.final_price)

        if base > 0 and final_int < base:
            discount = base - final_int
            percent = (discount * 100 + base // 2) // base
            return max(0, min(100, percent))

        return 0
    
    @property
    def has_discount(self):
        """Indica si el producto tiene descuento"""
        base = int(self.price or 0)
        return int(self.final_price) < base

    @property
    def final_price_display(self):
        """Precio final formateado en CLP para uso en admin/templates"""
        return format_clp(self.final_price)
    
    # PROPIEDADES DE INVENTARIO
    @property
    def stock_available(self):
        """Stock disponible para venta = total - reservado"""
        return max(0, self.stock_qty - self.stock_reserved)
    
    @property
    def is_low_stock(self):
        """¿Stock disponible está bajo?"""
        return self.stock_available <= self.low_stock_threshold
    
    @property
    def is_in_stock(self):
        """¿Hay stock disponible O se permiten backorders?"""
        return self.stock_available > 0 or self.allow_backorder
    
    def can_reserve(self, quantity):
        """¿Se puede reservar esta cantidad?"""
        if self.allow_backorder:
            return True
        return self.stock_available >= quantity
    
    def reserve_stock(self, quantity, reason='order', reference_id=None):
        """
        Reserva stock de forma atómica.
        Debe llamarse dentro de transaction.atomic()
        """
        from django.db import transaction
        from django.core.exceptions import ValidationError
        from django.apps import apps
        
        # Lock de fila para prevenir race conditions
        product = Product.objects.select_for_update().get(pk=self.pk)
        
        if not product.can_reserve(quantity):
            raise ValidationError(
                f"Stock insuficiente para {product.name}. "
                f"Disponible: {product.stock_available}, Solicitado: {quantity}"
            )
        
        product.stock_reserved += quantity
        product.save(update_fields=['stock_reserved'])
        
        # Registrar movimiento (si existe InventoryMovement)
        try:
            InventoryMovement = apps.get_model('products', 'InventoryMovement')
            InventoryMovement.objects.create(
                product=product,
                movement_type='reserve',
                quantity_change=quantity,
                quantity_after=product.stock_available,
                reason=reason,
                reference_id=reference_id
            )
        except Exception:
            pass  # Si no existe el modelo aún, continuar
        
        return product
    
    def release_stock(self, quantity, reason='cancel', reference_id=None):
        """Libera stock reservado"""
        from django.db import transaction
        from django.apps import apps
        
        product = Product.objects.select_for_update().get(pk=self.pk)
        product.stock_reserved = max(0, product.stock_reserved - quantity)
        product.save(update_fields=['stock_reserved'])
        
        # Registrar movimiento
        try:
            InventoryMovement = apps.get_model('products', 'InventoryMovement')
            InventoryMovement.objects.create(
                product=product,
                movement_type='release',
                quantity_change=-quantity,
                quantity_after=product.stock_available,
                reason=reason,
                reference_id=reference_id
            )
        except Exception:
            pass
        
        return product
    
    def confirm_sale(self, quantity, reason='sale', reference_id=None):
        """
        Confirma venta: decrementa stock_qty y stock_reserved.
        Llamar cuando orden está completada/enviada.
        """
        from django.db import transaction
        from django.apps import apps
        
        product = Product.objects.select_for_update().get(pk=self.pk)
        product.stock_qty -= quantity
        product.stock_reserved -= quantity
        product.save(update_fields=['stock_qty', 'stock_reserved'])
        
        # Registrar movimiento
        try:
            InventoryMovement = apps.get_model('products', 'InventoryMovement')
            InventoryMovement.objects.create(
                product=product,
                movement_type='sale',
                quantity_change=-quantity,
                quantity_after=product.stock_available,
                reason=reason,
                reference_id=reference_id
            )
        except Exception:
            pass
        
        return product


class ProductImage(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='images',
        verbose_name='Producto'
    )
    url = models.CharField(max_length=500, db_column='url', verbose_name='URL')
    alt_text = models.CharField(max_length=255, null=True, blank=True, db_column='alt_text', verbose_name='Texto alternativo')
    position = models.PositiveIntegerField(default=0, db_column='position', verbose_name='Posición')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')

    class Meta:
        db_table = 'product_images'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'
        indexes = [
            models.Index(fields=['product', 'position'], name='idx_product_position'),
        ]
        ordering = ['position']

    def __str__(self):
        return f"{self.product.name} - Imagen {self.position}"


class ProductPriceHistory(models.Model):
    """
    Historial inmutable de cambios de precios de productos.
    Permite rastrear evolución de precios a lo largo del tiempo para análisis y auditoría.
    """
    id = models.BigAutoField(primary_key=True, db_column='id')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='price_history',
        verbose_name='Producto'
    )
    
    # Precio base
    price = models.PositiveIntegerField(db_column='price', verbose_name='Precio base')
    
    # Campos de descuento (snapshot del estado al momento del cambio)
    discount_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='discount_price',
        verbose_name='Precio final del descuento'
    )
    discount_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='discount_amount',
        verbose_name='Monto a descontar'
    )
    discount_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_column='discount_percent',
        verbose_name='Descuento por porcentaje (%)'
    )
    
    # Precio final calculado (para consultas rápidas)
    final_price = models.PositiveIntegerField(
        db_column='final_price',
        verbose_name='Precio final',
        help_text='Precio final calculado al momento del cambio'
    )
    
    # Rango de vigencia (effective_from es cuando se aplicó este precio)
    effective_from = models.DateTimeField(
        db_column='effective_from',
        verbose_name='Vigente desde',
        help_text='Fecha y hora en que este precio entró en vigencia'
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        db_column='effective_to',
        verbose_name='Vigente hasta',
        help_text='Fecha y hora en que este precio dejó de estar vigente (NULL = precio actual)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    
    class Meta:
        db_table = 'product_price_history'
        verbose_name = 'Historial de Precio'
        verbose_name_plural = 'Historial de Precios'
        indexes = [
            models.Index(fields=['product', 'effective_from'], name='idx_price_history_product_date'),
            models.Index(fields=['product', 'effective_to'], name='idx_price_history_product_to'),
            models.Index(fields=['effective_from'], name='idx_price_history_from'),
            models.Index(fields=['effective_to'], name='idx_price_history_to'),
        ]
        ordering = ['-effective_from']
    
    def __str__(self):
        price_display = f"${self.final_price:,}" if self.final_price else "N/A"
        return f"{self.product.name} - {price_display} ({self.effective_from.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_current(self):
        """Indica si este es el precio actual (effective_to es NULL)"""
        return self.effective_to is None
    
    @property
    def duration_days(self):
        """Duración en días que estuvo vigente este precio"""
        if self.effective_to:
            delta = self.effective_to - self.effective_from
            return delta.days
        # Si es el precio actual, calcular hasta ahora
        from django.utils import timezone
        delta = timezone.now() - self.effective_from
        return delta.days


class InventoryMovement(models.Model):
    """
    Auditoría de movimientos de inventario.
    Registra TODOS los cambios: compras, ventas, ajustes, reservas, liberaciones.
    """
    
    MOVEMENT_TYPE_CHOICES = [
        ('purchase', 'Compra/Ingreso'),
        ('sale', 'Venta'),
        ('return', 'Devolución'),
        ('adjustment', 'Ajuste Manual'),
        ('reserve', 'Reserva'),
        ('release', 'Liberación de Reserva'),
        ('damage', 'Pérdida/Daño'),
    ]
    
    id = models.BigAutoField(primary_key=True, db_column='id')
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='inventory_movements',
        verbose_name='Producto'
    )
    
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        db_column='movement_type',
        verbose_name='Tipo de movimiento'
    )
    quantity_change = models.IntegerField(db_column='quantity_change', verbose_name='Cambio de cantidad')
    quantity_after = models.IntegerField(db_column='quantity_after', verbose_name='Cantidad después')
    
    reason = models.CharField(max_length=255, blank=True, db_column='reason', verbose_name='Razón')
    reference_id = models.IntegerField(null=True, blank=True, db_column='reference_id', verbose_name='ID de referencia')
    reference_type = models.CharField(max_length=50, blank=True, db_column='reference_type', verbose_name='Tipo de referencia')
    
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='created_by_id',
        related_name='inventory_movements',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    
    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        indexes = [
            models.Index(fields=['product', '-created_at'], name='idx_inventory_product'),
            models.Index(fields=['movement_type', '-created_at'], name='idx_inventory_type'),
            models.Index(fields=['reference_type', 'reference_id'], name='idx_inventory_reference'),
        ]
    
    def __str__(self):
        sign = '+' if self.quantity_change > 0 else ''
        return f"{self.product.name}: {sign}{self.quantity_change} ({self.movement_type})"

