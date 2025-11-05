from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, unique=True, db_column='name', verbose_name='Nombre')
    slug = models.SlugField(max_length=150, unique=True, db_column='slug', verbose_name='URL amigable')
    description = models.TextField(null=True, blank=True, db_column='description', verbose_name='Descripción')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

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
        related_name='products'
    )
    name = models.CharField(max_length=200, db_column='name')
    slug = models.SlugField(max_length=200, unique=True, db_column='slug')
    description = models.TextField(null=True, blank=True, db_column='description')
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column='price')
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='discount_price',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Precio con descuento. Si está configurado, se usa en lugar de price.'
    )
    stock_qty = models.PositiveIntegerField(default=0, db_column='stock_qty')
    brand = models.CharField(max_length=100, null=True, blank=True, db_column='brand')
    sku = models.CharField(max_length=64, unique=True, db_column='sku')
    active = models.BooleanField(default=True, db_column='active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

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
        # Validar que discount_price no sea mayor que price
        if self.discount_price and self.discount_price > self.price:
            raise ValueError('El precio de descuento no puede ser mayor que el precio original')
        super().save(*args, **kwargs)
    
    @property
    def final_price(self):
        """Precio final: discount_price si existe, sino price"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def discount_percent(self):
        """Porcentaje de descuento calculado automáticamente"""
        if self.discount_price and self.price > 0:
            discount = self.price - self.discount_price
            return round((discount / self.price) * 100, 2)
        return Decimal('0.00')
    
    @property
    def has_discount(self):
        """Indica si el producto tiene descuento"""
        return bool(self.discount_price and self.discount_price < self.price)


class ProductImage(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='images'
    )
    url = models.CharField(max_length=500, db_column='url')
    alt_text = models.CharField(max_length=255, null=True, blank=True, db_column='alt_text')
    position = models.PositiveIntegerField(default=0, db_column='position')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'product_images'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'
        indexes = [
            models.Index(fields=['product', 'position'], name='idx_product_position'),
        ]
        ordering = ['position']

    def __str__(self):
        return f"{self.product.name} - Image {self.position}"

