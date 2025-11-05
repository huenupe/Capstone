from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'table_name', 'record_id', 'ip_address', 'created_at')
    list_filter = ('action', 'table_name', 'created_at')
    search_fields = ('user__email', 'table_name', 'action')
    readonly_fields = ('id', 'user', 'action', 'table_name', 'record_id', 
                      'old_values', 'new_values', 'ip_address', 'created_at')
    
    def user(self, obj):
        return obj.user.email if obj.user else 'Anónimo'
    user.short_description = 'Usuario'
    user.admin_order_field = 'user__email'
    
    def action(self, obj):
        return obj.action
    action.short_description = 'Acción'
    action.admin_order_field = 'action'
    
    def table_name(self, obj):
        return obj.table_name
    table_name.short_description = 'Nombre de tabla'
    table_name.admin_order_field = 'table_name'
    
    def record_id(self, obj):
        return obj.record_id or '-'
    record_id.short_description = 'ID del registro'
    record_id.admin_order_field = 'record_id'
    
    def ip_address(self, obj):
        return obj.ip_address or '-'
    ip_address.short_description = 'Dirección IP'
    ip_address.admin_order_field = 'ip_address'
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d de %B de %Y a las %H:%M') if obj.created_at else '-'
    created_at.short_description = 'Creado el'
    created_at.admin_order_field = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

