from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    # Remover filter_horizontal porque User no tiene groups ni user_permissions
    filter_horizontal = ()
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Dirección', {'fields': ('street', 'city', 'region', 'postal_code')}),
        ('Permisos', {'fields': ('role', 'is_active')}),
        ('Fechas', {'fields': ('created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Traducir headers de columnas
    def email(self, obj):
        return obj.email
    email.short_description = 'Correo electrónico'
    email.admin_order_field = 'email'
    
    def first_name(self, obj):
        return obj.first_name or '-'
    first_name.short_description = 'Nombre'
    first_name.admin_order_field = 'first_name'
    
    def last_name(self, obj):
        return obj.last_name or '-'
    last_name.short_description = 'Apellidos'
    last_name.admin_order_field = 'last_name'
    
    def role(self, obj):
        return obj.get_role_display() if hasattr(obj, 'get_role_display') else obj.role
    role.short_description = 'Rol'
    role.admin_order_field = 'role'
    
    def is_active(self, obj):
        return obj.is_active
    is_active.short_description = 'Activo'
    is_active.boolean = True
    is_active.admin_order_field = 'is_active'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'token_value', 'created_at_display', 'expires_at_display', 'used_at_display', 'is_valid')
    list_filter = ('created_at', 'expires_at', 'used_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at', 'used_at')
    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'Usuario'
    user_email.admin_order_field = 'user__email'

    def token_value(self, obj):
        return str(obj.token)
    token_value.short_description = 'Token'
    token_value.admin_order_field = 'token'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%d de %B de %Y %H:%M') if obj.created_at else '-'
    created_at_display.short_description = 'Creado el'
    created_at_display.admin_order_field = 'created_at'

    def expires_at_display(self, obj):
        return obj.expires_at.strftime('%d de %B de %Y %H:%M') if obj.expires_at else '-'
    expires_at_display.short_description = 'Expira el'
    expires_at_display.admin_order_field = 'expires_at'

    def used_at_display(self, obj):
        return obj.used_at.strftime('%d de %B de %Y %H:%M') if obj.used_at else '-'
    used_at_display.short_description = 'Usado el'
    used_at_display.admin_order_field = 'used_at'

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Válido'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'street', 'city', 'region', 'is_default', 'created_at')
    list_filter = ('region', 'is_default', 'created_at')
    search_fields = ('user__email', 'street', 'city', 'region', 'label')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-is_default', '-created_at')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Dirección', {
            'fields': ('label', 'street', 'number', 'apartment', 'city', 'region', 'postal_code', 'is_default')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user(self, obj):
        return obj.user.email if obj.user else '-'
    user.short_description = 'Usuario'
    user.admin_order_field = 'user__email'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'

