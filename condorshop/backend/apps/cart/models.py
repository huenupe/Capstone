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
        """
        Obtiene o crea un carrito para un usuario o sesión.
        
        ✅ CORRECCIÓN: Maneja race conditions y múltiples carritos activos:
        - Usa get_or_create de forma atómica para evitar IntegrityError
        - Si hay múltiples carritos activos, usa el más reciente
        - Desactiva los carritos más antiguos para evitar duplicados
        """
        from django.db import IntegrityError, transaction
        import uuid
        
        if user:
            # Primero verificar si hay múltiples carritos activos y limpiarlos
            active_carts = cls.objects.filter(user=user, is_active=True).order_by('-created_at')
            if active_carts.count() > 1:
                # Desactivar todos excepto el más reciente
                cart = active_carts.first()
                active_carts.exclude(id=cart.id).update(is_active=False)
                return cart, False
            
            # Usar get_or_create de forma atómica
            # Buscar primero por user + is_active=True
            cart = cls.objects.filter(user=user, is_active=True).first()
            if cart:
                return cart, False
            
            # Si no existe, crear uno nuevo
            try:
                cart, created = cls.objects.get_or_create(
                    user=user,
                    is_active=True,
                    defaults={'session_token': None}
                )
                return cart, created
            except IntegrityError:
                # Race condition: otro proceso creó el carrito, obtenerlo
                cart = cls.objects.filter(user=user, is_active=True).first()
                if cart:
                    return cart, False
                raise
                
        elif session_token:
            # Primero verificar si hay múltiples carritos activos y limpiarlos
            active_carts = cls.objects.filter(session_token=session_token, is_active=True).order_by('-created_at')
            if active_carts.count() > 1:
                # Desactivar todos excepto el más reciente
                cart = active_carts.first()
                active_carts.exclude(id=cart.id).update(is_active=False)
                return cart, False
            
            # Buscar primero si ya existe un carrito con este token activo
            cart = cls.objects.filter(session_token=session_token, is_active=True).first()
            if cart:
                return cart, False
            
            # Verificar si hay un carrito inactivo con este token (reactivarlo)
            inactive_cart = cls.objects.filter(session_token=session_token, is_active=False).order_by('-created_at').first()
            if inactive_cart:
                inactive_cart.is_active = True
                inactive_cart.save(update_fields=['is_active'])
                return inactive_cart, False
            
            # Si no existe, crear uno nuevo usando get_or_create de forma atómica
            try:
                cart, created = cls.objects.get_or_create(
                    session_token=session_token,
                    defaults={'is_active': True, 'user': None}
                )
                # Si el carrito ya existía pero estaba inactivo, reactivarlo
                if not created and not cart.is_active:
                    cart.is_active = True
                    cart.save(update_fields=['is_active'])
                return cart, created
            except IntegrityError:
                # Race condition: otro proceso creó el carrito, obtenerlo
                cart = cls.objects.filter(session_token=session_token, is_active=True).first()
                if cart:
                    return cart, False
                # Si no está activo, reactivarlo
                cart = cls.objects.filter(session_token=session_token).order_by('-created_at').first()
                if cart:
                    cart.is_active = True
                    cart.save(update_fields=['is_active'])
                    return cart, False
                raise
        else:
            # Crear carrito nuevo con token de sesión único
            # Generar token único y crear carrito
            max_retries = 5
            for attempt in range(max_retries):
                new_token = str(uuid.uuid4())
                try:
                    cart, created = cls.objects.get_or_create(
                        session_token=new_token,
                        is_active=True,
                        defaults={'user': None}
                    )
                    return cart, created
                except IntegrityError:
                    # Token duplicado (muy improbable pero posible), generar nuevo
                    if attempt == max_retries - 1:
                        raise
                    continue


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

