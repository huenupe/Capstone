import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Sobrescribir username para hacerlo nullable (no se usa, pero AbstractUser lo requiere)
    username = models.CharField(max_length=150, blank=True, null=True, db_column='username')
    
    # Sobrescribir email para hacerlo único y usar db_column
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_column='email',
        validators=[EmailValidator()],
        verbose_name='Correo electrónico'
    )
    
    # Campos personalizados
    role = models.CharField(
        max_length=10,
        choices=[('cliente', 'Cliente'), ('admin', 'Admin')],
        default='cliente',
        db_column='role',
        verbose_name='Rol'
    )
    phone = models.CharField(max_length=50, blank=True, null=True, db_column='phone', verbose_name='Teléfono')
    
    # Dirección integrada
    street = models.CharField(max_length=200, blank=True, null=True, db_column='street', verbose_name='Calle')
    city = models.CharField(max_length=100, blank=True, null=True, db_column='city', verbose_name='Ciudad')
    region = models.CharField(max_length=100, blank=True, null=True, db_column='region', verbose_name='Región')
    postal_code = models.CharField(max_length=20, blank=True, null=True, db_column='postal_code', verbose_name='Código postal')

    # Campos de fecha personalizados (AbstractUser ya tiene date_joined, pero necesitamos created_at/updated_at)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email'], name='idx_email'),
            models.Index(fields=['role'], name='idx_role'),
        ]

    def __str__(self):
        return self.email

    def is_admin(self):
        return self.role == 'admin'


def _default_reset_expiration():
    timeout_hours = getattr(settings, 'PASSWORD_RESET_TIMEOUT_HOURS', 1)
    return timezone.now() + timedelta(hours=timeout_hours)


class PasswordResetToken(models.Model):
    """Token para recuperación de contraseña"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='password_reset_tokens',
        verbose_name='Usuario'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_column='token',
        verbose_name='Token'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    expires_at = models.DateTimeField(default=_default_reset_expiration, db_column='expires_at', verbose_name='Expira el')
    used_at = models.DateTimeField(null=True, blank=True, db_column='used_at', verbose_name='Usado el')

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Token de Restablecimiento de Contraseña'
        verbose_name_plural = 'Tokens de Restablecimiento de Contraseña'
        indexes = [
            models.Index(fields=['expires_at'], name='idx_password_reset_expires'),
            models.Index(fields=['user', 'used_at'], name='idx_pwreset_user_used_at'),
        ]

    def __str__(self):
        return f"Token {self.token} para {self.user.email}"

    def is_valid(self):
        """Verifica si el token es válido y no ha expirado"""
        return self.used_at is None and timezone.now() < self.expires_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])


class Address(models.Model):
    """Direcciones guardadas para usuarios"""
    id = models.BigAutoField(primary_key=True, db_column='id')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='addresses',
        verbose_name='Usuario'
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_column='label',
        help_text='Nombre descriptivo para esta dirección (ej: "Casa", "Oficina")',
        verbose_name='Etiqueta'
    )
    street = models.CharField(max_length=200, db_column='street', verbose_name='Calle')
    number = models.CharField(max_length=20, blank=True, null=True, db_column='number', verbose_name='Número')
    apartment = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_column='apartment',
        help_text='Dpto/Casa/Oficina',
        verbose_name='Dpto/Casa/Oficina'
    )
    city = models.CharField(max_length=100, db_column='city', verbose_name='Comuna')
    region = models.CharField(max_length=100, db_column='region', verbose_name='Región')
    postal_code = models.CharField(max_length=20, blank=True, null=True, db_column='postal_code', verbose_name='Código postal')
    is_default = models.BooleanField(
        default=False,
        db_column='is_default',
        help_text='Marcar como dirección predeterminada',
        verbose_name='Predeterminada'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')

    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        indexes = [
            models.Index(fields=['user'], name='idx_address_user'),
            models.Index(fields=['user', 'is_default'], name='idx_address_user_default'),
        ]
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        address_parts = [self.street]
        if self.number:
            address_parts.append(self.number)
        if self.apartment:
            address_parts.append(f"Dpto {self.apartment}")
        address_str = ', '.join(address_parts)
        if self.label:
            return f"{self.label} - {address_str}, {self.city}"
        return f"{address_str}, {self.city}, {self.region}"
    
    def save(self, *args, **kwargs):
        # Si se marca como default, quitar default de otras direcciones del usuario
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

