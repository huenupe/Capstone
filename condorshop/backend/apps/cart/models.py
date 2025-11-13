from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.products.models import Product
import uuid


class Cart(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='carts',
        verbose_name='Usuario'
    )
    session_token = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_column='session_token',
        verbose_name='Token de sesión'
    )
    is_active = models.BooleanField(default=True, db_column='is_active', verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'carts'
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
        indexes = [
            models.Index(fields=['user'], name='idx_cart_user'),
            models.Index(fields=['session_token'], name='idx_cart_session'),
        ]

    def __str__(self):
        if self.user:
            return f"Carrito {self.id} - Usuario: {self.user.email}"
        return f"Carrito {self.id} - Sesión: {self.session_token}"

    @classmethod
    def get_or_create_cart(cls, user=None, session_token=None):
        """Obtiene o crea un carrito para un usuario o sesión"""
        if user:
            cart, created = cls.objects.get_or_create(
                user=user,
                is_active=True,
                defaults={'session_token': None}
            )
        elif session_token:
            cart, created = cls.objects.get_or_create(
                session_token=session_token,
                is_active=True,
                defaults={'user': None}
            )
        else:
            # Crear carrito nuevo con token de sesión
            session_token = str(uuid.uuid4())
            cart = cls.objects.create(session_token=session_token, is_active=True)
            created = True
        return cart, created


class CartItem(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        db_column='cart_id',
        related_name='items',
        verbose_name='Carrito'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='cart_items',
        verbose_name='Producto'
    )
    quantity = models.PositiveIntegerField(db_column='quantity', verbose_name='Cantidad')
    unit_price = models.PositiveIntegerField(
        db_column='unit_price',
        verbose_name='Precio unitario'
    )
    total_price = models.PositiveIntegerField(
        db_column='total_price',
        verbose_name='Precio total'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Item de Carrito'
        verbose_name_plural = 'Items de Carrito'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='uq_cartitem_cart_product'
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name='quantity_positive'
            ),
        ]
        indexes = [
            models.Index(fields=['cart', 'product'], name='idx_cartitem_cart_product'),
            models.Index(fields=['product'], name='idx_cartitem_product'),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def save(self, *args, **kwargs):
        self.unit_price = int(self.unit_price or 0)
        self.quantity = int(self.quantity or 0)
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.total_price

