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
    discount_price = models.IntegerField(
        null=True,
        blank=True,
        db_column='discount_price',
        validators=[MinValueValidator(0)],
        help_text='Precio final después del descuento en pesos chilenos (CLP, sin decimales). Si está configurado, se usa este precio directamente. Ejemplo: 22990',
        verbose_name='Precio final del descuento'
    )
    discount_amount = models.IntegerField(
        null=True,
        blank=True,
        db_column='discount_amount',
        validators=[MinValueValidator(0)],
        help_text='Monto fijo a descontar del precio en pesos chilenos (CLP, sin decimales). Ejemplo: si el precio es $100000 y aquí pones $20000, el precio final será $80000.',
        verbose_name='Monto a descontar'
    )
    discount_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_column='discount_percent',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Porcentaje de descuento. Ingresa solo un número entero entre 1 y 100 (ej: 20 para 20%, 25 para 25%). No se aceptan decimales.',
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
        
        # Convertir price a entero para comparaciones
        price_int = int(self.price)
        
        # Validaciones de descuentos
        if self.discount_price is not None:
            if self.discount_price > price_int:
                raise ValueError('El precio final del descuento no puede ser mayor que el precio original')
            if self.discount_price < 0:
                raise ValueError('El precio final del descuento no puede ser negativo')
        
        if self.discount_amount is not None:
            if self.discount_amount > price_int:
                raise ValueError('El monto a descontar no puede ser mayor que el precio original')
            if self.discount_amount < 0:
                raise ValueError('El monto a descontar no puede ser negativo')
        
        if self.discount_percent is not None:
            if self.discount_percent < 1 or self.discount_percent > 100:
                raise ValueError('El porcentaje de descuento debe estar entre 1 y 100')
        
        # Si hay múltiples métodos de descuento, priorizar: discount_price > discount_amount > discount_percent
        # Si se configuró discount_price, limpiar los otros
        if self.discount_price is not None:
            self.discount_amount = None
            self.discount_percent = None
        # Si se configuró discount_amount, limpiar discount_percent
        elif self.discount_amount is not None:
            self.discount_percent = None
        
        super().save(*args, **kwargs)
    
    @property
    def final_price(self):
        """
        Calcula el precio final según el método de descuento configurado.
        Prioridad: discount_price > discount_amount > discount_percent > price
        Siempre retorna un entero (peso chileno, sin decimales)
        """
        price_int = int(self.price)
        
        # Prioridad 1: Precio final directo
        if self.discount_price is not None:
            final = max(self.discount_price, 0)  # No permitir precios negativos
            if final > price_int:
                # Si hay inconsistencia, normalizar al precio original
                return price_int
            return Decimal(str(final))
        
        # Prioridad 2: Monto a descontar
        if self.discount_amount is not None:
            final = price_int - self.discount_amount
            return Decimal(str(max(final, 0)))  # No permitir precios negativos
        
        # Prioridad 3: Porcentaje de descuento
        if self.discount_percent is not None:
            # Calcular: precio * (100 - porcentaje) / 100, redondeado a entero
            final = round(price_int * (100 - self.discount_percent) / 100)
            return Decimal(str(max(final, 0)))  # No permitir precios negativos
        
        # Sin descuento: retornar precio original (entero)
        return Decimal(str(price_int))
    
    @property
    def calculated_discount_percent(self):
        """
        Porcentaje de descuento calculado automáticamente basado en el precio final.
        Retorna un entero (1-100)
        """
        price_int = int(self.price)
        final_int = int(self.final_price)
        
        if price_int > 0 and final_int < price_int:
            discount = price_int - final_int
            percent = round((discount / price_int) * 100)
            return max(1, min(100, percent))  # Asegurar entre 1 y 100
        
        return 0
    
    @property
    def has_discount(self):
        """Indica si el producto tiene descuento"""
        return int(self.final_price) < int(self.price)


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

