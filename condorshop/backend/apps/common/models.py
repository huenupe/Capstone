from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinLengthValidator


class StoreConfig(models.Model):
    """
    Configuración global del sistema.
    Permite cambiar parámetros sin modificar código.
    """
    
    DATA_TYPE_CHOICES = [
        ('string', 'Texto'),
        ('int', 'Número Entero'),
        ('decimal', 'Número Decimal'),
        ('boolean', 'Booleano'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(
        max_length=50,
        unique=True,
        primary_key=True,
        db_column='key',
        verbose_name='Clave'
    )
    value = models.TextField(
        db_column='value',
        verbose_name='Valor'
    )
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='string',
        db_column='data_type',
        verbose_name='Tipo de dato'
    )
    description = models.TextField(
        blank=True,
        db_column='description',
        help_text="Descripción de qué hace este parámetro",
        verbose_name='Descripción'
    )
    
    is_public = models.BooleanField(
        default=False,
        db_column='is_public',
        help_text="Si es True, puede exponerse en API pública",
        verbose_name='Público'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        verbose_name='Actualizado el'
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='updated_by_id',
        related_name='config_changes',
        verbose_name='Actualizado por'
    )
    
    class Meta:
        db_table = 'store_config'
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    def get_value(self):
        """Convierte value según data_type"""
        import json
        from decimal import Decimal
        
        if self.data_type == 'int':
            return int(self.value)
        elif self.data_type == 'decimal':
            return Decimal(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes']
        elif self.data_type == 'json':
            return json.loads(self.value)
        return self.value
    
    @classmethod
    def get(cls, key, default=None):
        """
        Obtiene configuración con cache.
        
        Usage:
            tax_rate = StoreConfig.get('tax_rate', default=19)
        """
        cache_key = f'config:{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                config = cls.objects.get(key=key)
                value = config.get_value()
                cache.set(cache_key, value, timeout=3600)  # 1 hora
            except cls.DoesNotExist:
                value = default
        
        return value
    
    def save(self, *args, **kwargs):
        """Invalida cache al guardar"""
        super().save(*args, **kwargs)
        cache.delete(f'config:{self.key}')


class HeroCarouselSlide(models.Model):
    """
    Slides del carrusel principal (Hero Carousel)
    Permite gestionar las imágenes del carrusel desde el admin
    """
    
    name = models.CharField(
        max_length=100,
        db_column='name',
        verbose_name='Nombre',
        help_text='Nombre descriptivo del slide (ej: "Ofertas de Verano")'
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_column='description',
        verbose_name='Descripción',
        help_text='Descripción breve del slide (opcional)'
    )
    
    image = models.ImageField(
        upload_to='hero_carousel/',
        db_column='image',
        verbose_name='Imagen',
        help_text='Imagen del slide. Se recomienda formato 1920x480px o similar (relación 4:1). Máximo 5MB.',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])
        ]
    )
    
    alt_text = models.CharField(
        max_length=200,
        db_column='alt_text',
        verbose_name='Texto alternativo',
        help_text='Texto alternativo para accesibilidad (usado como alt de la imagen)',
        validators=[MinLengthValidator(3)]
    )
    
    order = models.PositiveIntegerField(
        default=0,
        db_column='order',
        verbose_name='Orden',
        help_text='Orden de visualización (menor número = aparece primero)'
    )
    
    is_active = models.BooleanField(
        default=True,
        db_column='is_active',
        verbose_name='Activo',
        help_text='Si está desactivado, no se mostrará en el carrusel'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        verbose_name='Creado el'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        verbose_name='Actualizado el'
    )
    
    class Meta:
        db_table = 'hero_carousel_slides'
        verbose_name = 'Slide del Carrusel'
        verbose_name_plural = 'Slides del Carrusel'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['is_active', 'order'], name='idx_hero_slide_active_order'),
            models.Index(fields=['created_at'], name='idx_hero_slide_created'),
        ]
    
    def __str__(self):
        return f"{self.name} (Orden: {self.order})"
    
    def clean(self):
        """Validaciones del modelo"""
        # Validar que alt_text no esté vacío o solo espacios
        if not self.alt_text or not self.alt_text.strip():
            raise ValidationError({
                'alt_text': 'El texto alternativo es obligatorio para accesibilidad'
            })
        
        # Validar tamaño de imagen (máximo 5MB)
        if self.image and hasattr(self.image, 'size'):
            max_size = 5 * 1024 * 1024  # 5MB
            if self.image.size > max_size:
                size_mb = self.image.size / 1024 / 1024
                raise ValidationError({
                    'image': f'La imagen no puede ser mayor a 5MB. Tamaño actual: {size_mb:.2f}MB'
                })
    
    def save(self, *args, **kwargs):
        """Guardar y limpiar caché"""
        self.full_clean()  # Ejecutar validaciones
        super().save(*args, **kwargs)
        # Invalidar caché del carrusel
        cache.delete('hero_carousel_slides')
    
    def delete(self, *args, **kwargs):
        """Eliminar y limpiar caché"""
        super().delete(*args, **kwargs)
        # Invalidar caché del carrusel
        cache.delete('hero_carousel_slides')

