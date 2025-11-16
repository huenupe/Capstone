from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from apps.common.utils import format_clp
from .models import Category, Product, ProductImage, ProductPriceHistory, InventoryMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'level', 'sort_order', 'active', 'full_path_display', 'image_preview', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('parent_category', 'active', 'level', 'created_at')
    fields = ('name', 'slug', 'parent_category', 'level', 'sort_order', 'active', 'description', 'image')
    autocomplete_fields = ['parent_category']  # Para búsqueda rápida de categorías padre
    readonly_fields = ('level',)  # level se calcula automáticamente
    
    def get_queryset(self, request):
        """Optimizar queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('parent_category')
    
    def name(self, obj):
        return obj.name
    name.short_description = 'Nombre'
    name.admin_order_field = 'name'
    
    def parent_category(self, obj):
        return obj.parent_category.name if obj.parent_category else '-'
    parent_category.short_description = 'Categoría padre'
    parent_category.admin_order_field = 'parent_category__name'
    
    def full_path_display(self, obj):
        """Mostrar ruta completa de la categoría"""
        return obj.get_full_path()
    full_path_display.short_description = 'Ruta completa'
    
    def depth_display(self, obj):
        """Mostrar profundidad en la jerarquía"""
        depth = obj.get_depth()
        if depth == 0:
            return 'Raíz'
        return f'Nivel {depth}'
    depth_display.short_description = 'Nivel'
    depth_display.admin_order_field = 'parent_category'
    
    def slug(self, obj):
        return obj.slug
    slug.short_description = 'URL amigable'
    slug.admin_order_field = 'slug'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" alt="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;" />',
                obj.image.url,
                obj.name
            )
        return '-'
    image_preview.short_description = 'Imagen'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = 'Imagen'
    verbose_name_plural = 'Imágenes'


class ProductAdminForm(forms.ModelForm):
    """Form con validaciones estrictas para descuentos (enteros)"""
    
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'price': forms.NumberInput(attrs={
                'step': '1',
                'min': '0',
                'placeholder': 'Ej: 45990'
            }),
            'discount_price': forms.NumberInput(attrs={
                'step': '1',
                'min': '0',
                'placeholder': 'Ej: 22990'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'step': '1',
                'min': '0',
                'placeholder': 'Ej: 3000'
            }),
            'discount_percent': forms.NumberInput(attrs={
                'step': '1',
                'min': '1',
                'max': '100',
                'placeholder': 'Ej: 20 (para 20%)'
            }),
        }
    
    def clean_discount_percent(self):
        """Validar que discount_percent sea entero entre 1-100"""
        percent = self.cleaned_data.get('discount_percent')
        if percent is not None:
            # Verificar que sea entero
            if not isinstance(percent, int) and (isinstance(percent, float) and not percent.is_integer()):
                raise ValidationError('Ingresa un número entero entre 1 y 100. No se aceptan decimales (ej: 20, no 0.2 o 20.5).')
            if percent < 1 or percent > 100:
                raise ValidationError('El porcentaje de descuento debe estar entre 1 y 100.')
        return percent
    
    def clean_discount_price(self):
        """Validar que discount_price sea entero"""
        price = self.cleaned_data.get('discount_price')
        if price is not None:
            # Verificar que sea entero
            if not isinstance(price, int) and (isinstance(price, float) and not price.is_integer()):
                raise ValidationError('Ingresa un número entero en pesos chilenos (CLP, sin decimales). Ej: 22990, no 22990.50')
            if price < 0:
                raise ValidationError('El precio final del descuento no puede ser negativo.')
            # Si es 0, convertir a None (sin descuento)
            if price == 0:
                return None
        return price
    
    def clean_discount_amount(self):
        """Validar que discount_amount sea entero"""
        amount = self.cleaned_data.get('discount_amount')
        if amount is not None:
            # Verificar que sea entero
            if not isinstance(amount, int) and (isinstance(amount, float) and not amount.is_integer()):
                raise ValidationError('Ingresa un número entero en pesos chilenos (CLP, sin decimales). Ej: 3000, no 3000.50')
            if amount < 0:
                raise ValidationError('El monto a descontar no puede ser negativo.')
            # Si es 0, convertir a None (sin descuento)
            if amount == 0:
                return None
        return amount
    
    def clean(self):
        """Validaciones cruzadas"""
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        discount_amount = cleaned_data.get('discount_amount')
        
        if price:
            price_int = int(price)
            
            if discount_price is not None and discount_price > price_int:
                raise ValidationError({
                    'discount_price': 'El precio final del descuento no puede ser mayor que el precio original.'
                })
            
            if discount_amount is not None and discount_amount > price_int:
                raise ValidationError({
                    'discount_amount': 'El monto a descontar no puede ser mayor que el precio original.'
                })
        
        return cleaned_data


class ProductPriceHistoryInline(admin.TabularInline):
    """Inline para mostrar historial de precios en ProductAdmin"""
    model = ProductPriceHistory
    extra = 0
    readonly_fields = ('price', 'discount_price', 'discount_amount', 'discount_percent', 'final_price', 'effective_from', 'effective_to', 'duration_days_display', 'is_current_display')
    can_delete = False  # Historial es inmutable
    verbose_name = 'Registro de Precio'
    verbose_name_plural = 'Historial de Precios'
    ordering = ['-effective_from']
    max_num = 20  # Limitar a los últimos 20 cambios
    
    def duration_days_display(self, obj):
        """Mostrar duración en días"""
        if obj:
            days = obj.duration_days
            if days == 0:
                return "Hoy"
            elif days == 1:
                return "1 día"
            else:
                return f"{days} días"
        return "-"
    duration_days_display.short_description = 'Duración'
    
    def is_current_display(self, obj):
        """Indicar si es el precio actual"""
        return obj.is_current if obj else False
    is_current_display.boolean = True
    is_current_display.short_description = 'Actual'
    
    def has_add_permission(self, request, obj=None):
        """No permitir agregar manualmente (se crea automáticamente)"""
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'sku', 'category', 'price_clp', 'stock_info', 'active', 'created_at')
    list_filter = ('category', 'active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductPriceHistoryInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'category', 'description', 'brand', 'sku', 'active')
        }),
        ('Precio y Stock', {
            'fields': ('price_display', 'price', 'stock_qty', 'stock_reserved', 'stock_available_display', 'low_stock_threshold', 'allow_backorder', 'is_low_stock_display', 'is_in_stock_display')
        }),
        ('Descuentos', {
            'fields': ('discount_price_display', 'discount_price', 'discount_amount', 'discount_percent'),
            'description': 'Puedes usar uno de los tres métodos de descuento. Precedencia: Precio final > Monto > Porcentaje. Si configuras "Precio final del descuento", los otros se desactivarán automáticamente. Todos los valores deben ser enteros (CLP sin decimales para montos/precios, 1-100 para porcentaje).'
        }),
        ('Información Calculada', {
            'fields': ('final_price_display', 'calculated_discount_percent', 'has_discount'),
            'classes': ('collapse',),
            'description': 'Estos valores se calculan automáticamente basados en los descuentos configurados. Todos los precios se muestran como enteros en pesos chilenos (CLP).'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'price_display',
        'final_price_display',
        'discount_price_display',
        'calculated_discount_percent',
        'has_discount',
        'stock_available_display',
        'is_low_stock_display',
        'is_in_stock_display',
        'created_at',
        'updated_at',
    )
    
    def get_queryset(self, request):
        """Optimizar queries con select_related y prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('images')
    
    # Traducir headers de columnas
    def name(self, obj):
        return obj.name
    name.short_description = 'Nombre'
    name.admin_order_field = 'name'
    
    def sku(self, obj):
        return obj.sku
    sku.short_description = 'SKU'
    sku.admin_order_field = 'sku'
    
    def category(self, obj):
        return obj.category.name if obj.category else '-'
    category.short_description = 'Categoría'
    category.admin_order_field = 'category__name'
    
    def price_clp(self, obj):
        return format_clp(obj.price)
    price_clp.short_description = 'Precio (CLP)'
    price_clp.admin_order_field = 'price'

    def price_display(self, obj):
        if not obj:
            return format_clp(0)
        return format_clp(obj.price)
    price_display.short_description = 'Precio (CLP)'

    def discount_price_display(self, obj):
        if not obj or obj.discount_price is None:
            return '-'
        return format_clp(obj.discount_price)
    discount_price_display.short_description = 'Precio descuento (CLP)'
    
    def stock_qty(self, obj):
        return obj.stock_qty
    stock_qty.short_description = 'Cantidad en stock'
    stock_qty.admin_order_field = 'stock_qty'
    
    def active(self, obj):
        return obj.active
    active.short_description = 'Activo'
    active.boolean = True
    active.admin_order_field = 'active'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'
    
    # Métodos para campos calculados en readonly_fields
    def final_price_display(self, obj):
        """Muestra el precio final calculado"""
        if not obj:
            return format_clp(0)
        return format_clp(obj.final_price)
    final_price_display.short_description = 'Precio final (CLP)'
    
    def calculated_discount_percent(self, obj):
        """Muestra el porcentaje de descuento calculado (entero)"""
        percent = obj.calculated_discount_percent
        return f"{int(percent)}%" if percent > 0 else "0%"
    calculated_discount_percent.short_description = 'Descuento Calculado'
    
    def has_discount(self, obj):
        """Indica si tiene descuento"""
        return obj.has_discount
    has_discount.boolean = True
    has_discount.short_description = 'Tiene Descuento'
    
    def stock_info(self, obj):
        """Información de stock en listado"""
        return f"{obj.stock_qty} total / {obj.stock_reserved} reservado / {obj.stock_available} disponible"
    stock_info.short_description = 'Stock'
    
    def stock_available_display(self, obj):
        """Mostrar stock disponible"""
        return f"{obj.stock_available} unidades"
    stock_available_display.short_description = 'Stock Disponible'
    
    def is_low_stock_display(self, obj):
        """Indica si tiene stock bajo"""
        return obj.is_low_stock
    is_low_stock_display.boolean = True
    is_low_stock_display.short_description = 'Stock Bajo'
    
    def is_in_stock_display(self, obj):
        """Indica si está en stock"""
        return obj.is_in_stock
    is_in_stock_display.boolean = True
    is_in_stock_display.short_description = 'En Stock'


@admin.register(ProductPriceHistory)
class ProductPriceHistoryAdmin(admin.ModelAdmin):
    """Admin para historial de precios (vista independiente)"""
    list_display = ('product', 'final_price_display', 'price_display', 'discount_info', 'effective_from', 'effective_to', 'duration_days_display', 'is_current_display')
    list_filter = ('effective_from', 'effective_to', 'product__category')
    search_fields = ('product__name', 'product__sku')
    readonly_fields = ('product', 'price', 'discount_price', 'discount_amount', 'discount_percent', 'final_price', 'effective_from', 'effective_to', 'created_at', 'duration_days_display', 'is_current_display')
    
    def get_queryset(self, request):
        """Optimizar queries"""
        qs = super().get_queryset(request)
        return qs.select_related('product', 'product__category')
    
    def final_price_display(self, obj):
        """Mostrar precio final formateado"""
        return format_clp(obj.final_price) if obj else "-"
    final_price_display.short_description = 'Precio Final'
    final_price_display.admin_order_field = 'final_price'
    
    def price_display(self, obj):
        """Mostrar precio base formateado"""
        return format_clp(obj.price) if obj else "-"
    price_display.short_description = 'Precio Base'
    price_display.admin_order_field = 'price'
    
    def discount_info(self, obj):
        """Mostrar información de descuento"""
        if not obj:
            return "-"
        if obj.discount_price:
            return f"Precio fijo: {format_clp(obj.discount_price)}"
        elif obj.discount_amount:
            return f"Descuento: {format_clp(obj.discount_amount)}"
        elif obj.discount_percent:
            return f"Descuento: {obj.discount_percent}%"
        return "Sin descuento"
    discount_info.short_description = 'Descuento'
    
    def duration_days_display(self, obj):
        """Mostrar duración en días"""
        if obj:
            days = obj.duration_days
            if days == 0:
                return "Hoy"
            elif days == 1:
                return "1 día"
            else:
                return f"{days} días"
        return "-"
    duration_days_display.short_description = 'Duración'
    
    def is_current_display(self, obj):
        """Indicar si es el precio actual"""
        return obj.is_current if obj else False
    is_current_display.boolean = True
    is_current_display.short_description = 'Actual'
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente (se crea automáticamente)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar (historial es inmutable)"""
        return False


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    """Admin para movimientos de inventario"""
    list_display = ('product', 'movement_type', 'quantity_change_display', 'quantity_after', 'reason', 'reference_info', 'created_at')
    list_filter = ('movement_type', 'created_at', 'product__category')
    search_fields = ('product__name', 'product__sku', 'reason', 'reference_id')
    readonly_fields = ('product', 'movement_type', 'quantity_change', 'quantity_after', 'reason', 'reference_id', 'reference_type', 'created_by', 'created_at')
    
    def get_queryset(self, request):
        """Optimizar queries"""
        qs = super().get_queryset(request)
        return qs.select_related('product', 'product__category', 'created_by')
    
    def quantity_change_display(self, obj):
        """Mostrar cambio de cantidad con signo"""
        sign = '+' if obj.quantity_change > 0 else ''
        return f"{sign}{obj.quantity_change}"
    quantity_change_display.short_description = 'Cambio'
    quantity_change_display.admin_order_field = 'quantity_change'
    
    def reference_info(self, obj):
        """Mostrar información de referencia"""
        if obj.reference_id and obj.reference_type:
            return f"{obj.reference_type} #{obj.reference_id}"
        return "-"
    reference_info.short_description = 'Referencia'
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente (se crea automáticamente)"""
        return False
