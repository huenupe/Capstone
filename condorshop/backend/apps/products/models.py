from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=100, unique=True, db_column='name')
    slug = models.SlugField(max_length=150, unique=True, db_column='slug')
    description = models.TextField(null=True, blank=True, db_column='description')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
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
    stock_qty = models.PositiveIntegerField(default=0, db_column='stock_qty')
    brand = models.CharField(max_length=100, null=True, blank=True, db_column='brand')
    sku = models.CharField(max_length=64, unique=True, db_column='sku')
    active = models.BooleanField(default=True, db_column='active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'products'
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
        super().save(*args, **kwargs)


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
        indexes = [
            models.Index(fields=['product', 'position'], name='idx_product_position'),
        ]
        ordering = ['position']

    def __str__(self):
        return f"{self.product.name} - Image {self.position}"

