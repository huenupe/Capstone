from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import EmailValidator


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
        validators=[EmailValidator()]
    )
    
    # Campos personalizados
    role = models.CharField(
        max_length=10,
        choices=[('cliente', 'Cliente'), ('admin', 'Admin')],
        default='cliente',
        db_column='role'
    )
    phone = models.CharField(max_length=50, blank=True, null=True, db_column='phone')
    
    # Dirección integrada
    street = models.CharField(max_length=200, blank=True, null=True, db_column='street')
    city = models.CharField(max_length=100, blank=True, null=True, db_column='city')
    region = models.CharField(max_length=100, blank=True, null=True, db_column='region')
    postal_code = models.CharField(max_length=20, blank=True, null=True, db_column='postal_code')

    # Campos de fecha personalizados (AbstractUser ya tiene date_joined, pero necesitamos created_at/updated_at)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

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


class PasswordResetToken(models.Model):
    """Token para recuperación de contraseña"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='password_reset_tokens'
    )
    token = models.CharField(max_length=64, unique=True, db_column='token')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    expires_at = models.DateTimeField(db_column='expires_at')
    used = models.BooleanField(default=False, db_column='used')

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Token de Restablecimiento de Contraseña'
        verbose_name_plural = 'Tokens de Restablecimiento de Contraseña'
        indexes = [
            models.Index(fields=['token'], name='idx_reset_token'),
            models.Index(fields=['user', 'used'], name='idx_reset_user_used'),
        ]

    def __str__(self):
        return f"Token para {self.user.email}"

    def is_valid(self):
        """Verifica si el token es válido y no ha expirado"""
        from django.utils import timezone
        return not self.used and timezone.now() < self.expires_at

