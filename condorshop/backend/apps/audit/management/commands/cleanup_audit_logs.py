"""
Comando para limpiar registros antiguos de audit_logs.

Mantiene solo los registros de los últimos N meses (configurable).
Ayuda a mantener el tamaño de la base de datos bajo control.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = 'Elimina registros de audit_logs más antiguos que N meses (default: 6 meses)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=6,
            help='Cantidad de meses de retención (default: 6)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin eliminar realmente los registros',
        )

    def handle(self, *args, **options):
        months = options['months']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'🧹 Limpieza de audit_logs (retener últimos {months} meses)...\n'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN - No se eliminarán registros realmente\n'))
        
        # Calcular fecha de corte
        cutoff_date = timezone.now() - timedelta(days=months * 30)
        
        # Contar registros a eliminar
        logs_to_delete = AuditLog.objects.filter(created_at__lt=cutoff_date)
        count_to_delete = logs_to_delete.count()
        
        if count_to_delete == 0:
            self.stdout.write(self.style.SUCCESS('✅ No hay registros antiguos para eliminar'))
            return
        
        # Estadísticas antes de eliminar
        total_logs = AuditLog.objects.count()
        logs_to_keep = total_logs - count_to_delete
        
        self.stdout.write(f'📊 Estadísticas:')
        self.stdout.write(f'   Total de registros: {total_logs:,}')
        self.stdout.write(f'   Registros a eliminar: {count_to_delete:,} (anteriores a {cutoff_date.strftime("%Y-%m-%d")})')
        self.stdout.write(f'   Registros a mantener: {logs_to_keep:,}\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN - Se eliminarían {count_to_delete:,} registros'))
            self.stdout.write(self.style.SUCCESS('\n✅ Simulación completada. Ejecuta sin --dry-run para eliminar.'))
            return
        
        # Confirmar eliminación
        self.stdout.write(self.style.WARNING(f'⚠️  Se eliminarán {count_to_delete:,} registros'))
        
        # Eliminar registros
        deleted_count, _ = logs_to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Eliminados {deleted_count:,} registros de audit_logs'))
        self.stdout.write(self.style.SUCCESS(f'✅ Mantenidos {logs_to_keep:,} registros recientes'))
        
        # Recomendación
        self.stdout.write(self.style.MIGRATE_HEADING('\n💡 Recomendación:'))
        self.stdout.write('   Ejecutar este comando mensualmente con un cron job:')
        self.stdout.write('   python manage.py cleanup_audit_logs --months=6\n')

