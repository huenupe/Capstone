from django.db import models
from django.core.cache import cache


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

