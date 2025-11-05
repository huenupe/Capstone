from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Category(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, unique=True, db_column='name', verbose_name='Nombre')
    slug = models.SlugField(max_length=150, unique=True, db_column='slug', verbose_name='URL amigable')
    description = models.TextField(null=True, blank=True, db_column='description', verbose_name='Descripción')
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
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column='price', verbose_name='Precio')
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='discount_price',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Precio final después del descuento. Si está configurado, se usa este precio directamente.',
        verbose_name='Precio final del descuento'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='discount_amount',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Monto fijo a descontar del precio. Ejemplo: si el precio es $100 y aquí pones $20, el precio final será $80.',
        verbose_name='Monto a descontar'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='discount_percent',
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Porcentaje de descuento. Ingresa solo el número (ej: 20 para 20%, 25.5 para 25.5%).',
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
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Validaciones de descuentos
        if self.discount_price and self.discount_price > self.price:
            raise ValueError('El precio final del descuento no puede ser mayor que el precio original')
        
        if self.discount_amount and self.discount_amount > self.price:
            raise ValueError('El monto a descontar no puede ser mayor que el precio original')
        
        if self.discount_percent and (self.discount_percent < 0 or self.discount_percent > 100):
            raise ValueError('El porcentaje de descuento debe estar entre 0 y 100')
        
        # Si hay múltiples métodos de descuento, priorizar: discount_price > discount_amount > discount_percent
        # Si se configuró discount_price, limpiar los otros
        if self.discount_price:
            self.discount_amount = None
            self.discount_percent = None
        # Si se configuró discount_amount, limpiar discount_percent
        elif self.discount_amount:
            self.discount_percent = None
        
        super().save(*args, **kwargs)
    
    @property
    def final_price(self):
        """
        Calcula el precio final según el método de descuento configurado.
        Prioridad: discount_price > discount_amount > discount_percent > price
        """
        if self.discount_price:
            return self.discount_price
        
        if self.discount_amount:
            final = self.price - self.discount_amount
            return max(final, Decimal('0.00'))  # No permitir precios negativos
        
        if self.discount_percent:
            discount = (self.price * self.discount_percent) / Decimal('100.00')
            final = self.price - discount
            return max(final, Decimal('0.00'))  # No permitir precios negativos
        
        return self.price
    
    @property
    def calculated_discount_percent(self):
        """
        Porcentaje de descuento calculado automáticamente basado en el precio final
        """
        if self.price > 0:
            discount = self.price - self.final_price
            if discount > 0:
                return round((discount / self.price) * 100, 2)
        return Decimal('0.00')
    
    @property
    def has_discount(self):
        """Indica si el producto tiene descuento"""
        return self.final_price < self.price


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

