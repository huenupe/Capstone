from django.contrib import admin
from django.utils.html import format_html
from .models import HeroCarouselSlide


@admin.register(HeroCarouselSlide)
class HeroCarouselSlideAdmin(admin.ModelAdmin):
    """
    Admin para gestionar slides del carrusel principal
    """
    list_display = ['preview_image', 'name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'alt_text']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'alt_text')
        }),
        ('Imagen', {
            'fields': ('image', 'image_preview'),
            'description': 'Arrastra y suelta la imagen o haz clic en "Elegir archivo"'
        }),
        ('Configuración', {
            'fields': ('order', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_image(self, obj):
        """Muestra una miniatura de la imagen en la lista"""
        if obj.image:
            try:
                return format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 50px; object-fit: cover;" alt="{}" />',
                    obj.image.url,
                    obj.alt_text or 'Vista previa'
                )
            except (ValueError, AttributeError):
                return "Imagen no disponible"
        return "Sin imagen"
    preview_image.short_description = 'Vista previa'
    
    def image_preview(self, obj):
        """Muestra una vista previa más grande en el formulario"""
        if obj.image:
            try:
                return format_html(
                    '<img src="{}" style="max-width: 100%; max-height: 300px; object-fit: contain; border: 1px solid #ddd; padding: 10px; border-radius: 4px;" alt="{}" />',
                    obj.image.url,
                    obj.alt_text or 'Vista previa'
                )
            except (ValueError, AttributeError):
                return "Imagen no disponible"
        return "No hay imagen cargada"
    image_preview.short_description = 'Vista previa de la imagen'
    
    def get_queryset(self, request):
        """Optimizar queries para la lista"""
        # No hay relaciones ForeignKey, así que select_related no es necesario
        # Se mantiene para futuras optimizaciones si se agregan relaciones
        return super().get_queryset(request)

