from django.db import models
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
        related_name='carts'
    )
    session_token = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_column='session_token'
    )
    is_active = models.BooleanField(default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

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
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(db_column='quantity')
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column='unit_price'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Item de Carrito'
        verbose_name_plural = 'Items de Carrito'
        unique_together = [['cart', 'product']]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='quantity_positive'
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

