from django.contrib import admin
from .models import StoreConfig


@admin.register(StoreConfig)
class StoreConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'data_type', 'is_public', 'updated_at']
    list_filter = ['data_type', 'is_public']
    search_fields = ['key', 'description']
    readonly_fields = ['key', 'updated_at', 'updated_by']
    fields = ['key', 'value', 'data_type', 'description', 'is_public', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

