from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    verbose_name = 'Item'
    verbose_name_plural = 'Items'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_token', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    inlines = [CartItemInline]
    search_fields = ('user__email', 'session_token')
    
    def user(self, obj):
        return obj.user.email if obj.user else '-'
    user.short_description = 'Usuario'
    user.admin_order_field = 'user__email'
    
    def session_token(self, obj):
        return obj.session_token[:20] + '...' if obj.session_token and len(obj.session_token) > 20 else (obj.session_token or '-')
    session_token.short_description = 'Token de sesión'
    session_token.admin_order_field = 'session_token'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.short_description = 'Activo'
    is_active.boolean = True
    is_active.admin_order_field = 'is_active'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'

