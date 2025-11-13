from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from apps.common.utils import format_clp


class Category(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, unique=True, db_column='name', verbose_name='Nombre')
    slug = models.SlugField(max_length=150, unique=True, db_column='slug', verbose_name='URL amigable')
    description = models.TextField(null=True, blank=True, db_column='description', verbose_name='Descripción')
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
        indexes = [
            models.Index(fields=['slug'], name='idx_category_slug'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
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
    stock_qty = models.PositiveIntegerField(default=0, db_column='stock_qty', verbose_name='Cantidad en stock')
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

