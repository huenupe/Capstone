from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def name(self, obj):
        return obj.name
    name.short_description = 'Nombre'
    name.admin_order_field = 'name'
    
    def slug(self, obj):
        return obj.slug
    slug.short_description = 'URL amigable'
    slug.admin_order_field = 'slug'
    
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'sku', 'category', 'price', 'stock_qty', 'active', 'created_at')
    list_filter = ('category', 'active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'category', 'description', 'brand', 'sku', 'active')
        }),
        ('Precio y Stock', {
            'fields': ('price', 'stock_qty')
        }),
        ('Descuentos', {
            'fields': ('discount_price', 'discount_amount', 'discount_percent'),
            'description': 'Puedes usar uno de los tres métodos de descuento. Precedencia: Precio final > Monto > Porcentaje. Si configuras "Precio final del descuento", los otros se desactivarán automáticamente. Todos los valores deben ser enteros (CLP sin decimales para montos/precios, 1-100 para porcentaje).'
        }),
        ('Información Calculada', {
            'fields': ('final_price', 'calculated_discount_percent', 'has_discount'),
            'classes': ('collapse',),
            'description': 'Estos valores se calculan automáticamente basados en los descuentos configurados. Todos los precios se muestran como enteros en pesos chilenos (CLP).'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('final_price', 'calculated_discount_percent', 'has_discount', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')
    
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
    
    def price(self, obj):
        return f"${obj.price:,.0f}".replace(',', '.')
    price.short_description = 'Precio'
    price.admin_order_field = 'price'
    
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
    def final_price(self, obj):
        """Muestra el precio final calculado"""
        return f"${obj.final_price:,.0f}".replace(',', '.')
    final_price.short_description = 'Precio Final'
    
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

