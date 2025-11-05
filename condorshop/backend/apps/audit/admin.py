from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'table_name', 'record_id', 'ip_address', 'created_at')
    list_filter = ('action', 'table_name', 'created_at')
    search_fields = ('user__email', 'table_name', 'action')
    readonly_fields = ('id', 'user', 'action', 'table_name', 'record_id', 
                      'old_values', 'new_values', 'ip_address', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

