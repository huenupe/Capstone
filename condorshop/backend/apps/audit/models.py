from django.db import models
from django.conf import settings
import json


class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100, db_column='action')
    table_name = models.CharField(max_length=50, db_column='table_name')
    record_id = models.BigIntegerField(null=True, blank=True, db_column='record_id')
    old_values = models.JSONField(null=True, blank=True, db_column='old_values')
    new_values = models.JSONField(null=True, blank=True, db_column='new_values')
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_column='ip_address')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user'], name='idx_audit_user'),
            models.Index(fields=['table_name'], name='idx_audit_table'),
            models.Index(fields=['created_at'], name='idx_audit_created'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        return f"{self.action} on {self.table_name} by {user_info} at {self.created_at}"

