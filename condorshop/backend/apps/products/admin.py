from django.contrib import admin
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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
            'description': 'Puedes usar uno de los tres métodos de descuento. Si configuras "Precio final del descuento", los otros se desactivarán automáticamente. Si configuras "Monto a descontar", el porcentaje se desactivará.'
        }),
        ('Información Calculada', {
            'fields': ('final_price', 'calculated_discount_percent', 'has_discount'),
            'classes': ('collapse',),
            'description': 'Estos valores se calculan automáticamente basados en los descuentos configurados.'
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
        """Muestra el porcentaje de descuento calculado"""
        percent = obj.calculated_discount_percent
        return f"{percent:.2f}%" if percent > 0 else "0%"
    calculated_discount_percent.short_description = 'Descuento Calculado'
    
    def has_discount(self, obj):
        """Indica si tiene descuento"""
        return obj.has_discount
    has_discount.boolean = True
    has_discount.short_description = 'Tiene Descuento'

