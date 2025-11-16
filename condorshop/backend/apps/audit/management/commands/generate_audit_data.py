import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.audit.models import AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera datos de auditoría realistas para demo del dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Cantidad de registros a generar (default: 100)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Días hacia atrás para distribuir registros (default: 7)'
        )

    def handle(self, *args, **options):
        count = options['count']
        days = options['days']
        
        # Verificar que existe al menos un usuario
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR(
                'ERROR: No hay usuarios en la BD. Ejecuta: python manage.py load_initial_data'
            ))
            return

        self.stdout.write(self.style.WARNING(f'Generando {count} registros de auditoria...'))
        self.stdout.write(f'   Usuario: {user.email}')
        self.stdout.write(f'   Distribucion: ultimos {days} dias')

        # Configuración de datos (40% VIEW, 30% CREATE, 20% UPDATE, 10% DELETE)
        actions = (
            ['VIEW'] * 40 +
            ['CREATE'] * 30 +
            ['UPDATE'] * 20 +
            ['DELETE'] * 10
        )
        
        tables = [
            'products', 'orders', 'carts', 'users', 
            'payments', 'order_items', 'payment_transactions'
        ]
        
        # Generar registros
        audit_logs = []
        now = timezone.now()
        
        for i in range(count):
            # Fecha aleatoria en los últimos N días
            days_ago = random.randint(0, days - 1)
            hours = random.randint(8, 20)  # Entre 8 AM y 8 PM
            minutes = random.randint(0, 59)
            seconds = random.randint(0, 59)
            
            created_at = now - timedelta(
                days=days_ago,
                hours=random.randint(0, 16),  # Variación de horas
                minutes=minutes,
                seconds=seconds
            )
            
            # Seleccionar acción y tabla aleatoria
            action = random.choice(actions)
            table = random.choice(tables)
            record_id = random.randint(1, 9999)
            
            # Generar valores según el tipo de acción
            old_values = None
            new_values = None
            
            if action == 'CREATE':
                new_values = {
                    'name': f'Demo Item {record_id}',
                    'status': random.choice(['active', 'pending', 'draft']),
                    'created_by': user.email,
                    'demo_data': True  # Marca para identificar datos de prueba
                }
            elif action == 'UPDATE':
                old_values = {
                    'status': random.choice(['pending', 'draft']),
                    'quantity': random.randint(1, 10),
                    'price': round(random.uniform(10, 1000), 2)
                }
                new_values = {
                    'status': random.choice(['completed', 'active', 'cancelled']),
                    'quantity': random.randint(5, 50),
                    'price': round(random.uniform(10, 1000), 2)
                }
            elif action == 'DELETE':
                old_values = {
                    'name': f'Deleted Item {record_id}',
                    'status': 'active',
                    'deleted_at': str(created_at)
                }
            # VIEW no necesita old_values ni new_values
            
            # Crear objeto AuditLog (sin guardar todavía)
            audit_log = AuditLog(
                user=user,
                action=action,
                table_name=table,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                ip_address='127.0.0.1',
            )
            
            audit_logs.append(audit_log)
        
        # Guardar todos los registros en una sola operación (bulk_create)
        try:
            # NOTA: bulk_create no llama a save() ni señales, por lo que created_at
            # usará auto_now_add. Para fechas personalizadas, necesitamos guardar uno por uno.
            
            self.stdout.write(self.style.WARNING('   Guardando registros...'))
            
            created_count = 0
            for log in audit_logs:
                log.save()
                created_count += 1
                
                # Mostrar progreso cada 20 registros
                if created_count % 20 == 0:
                    self.stdout.write(f'   OK {created_count}/{count} registros creados')
            
            self.stdout.write(self.style.SUCCESS(f'\nOK: Se crearon {created_count} registros de auditoria'))
            
            # Mostrar distribución real
            view_count = AuditLog.objects.filter(action='VIEW').count()
            create_count = AuditLog.objects.filter(action='CREATE').count()
            update_count = AuditLog.objects.filter(action='UPDATE').count()
            delete_count = AuditLog.objects.filter(action='DELETE').count()
            
            self.stdout.write(self.style.SUCCESS('\nDistribucion en la base de datos:'))
            self.stdout.write(f'   VIEW: {view_count} registros')
            self.stdout.write(f'   CREATE: {create_count} registros')
            self.stdout.write(f'   UPDATE: {update_count} registros')
            self.stdout.write(f'   DELETE: {delete_count} registros')
            self.stdout.write(f'   TOTAL: {AuditLog.objects.count()} registros')
            
            self.stdout.write(self.style.WARNING('\nRecarga tu dashboard en el navegador (F5) para ver los cambios'))
            
            # Información para rollback
            self.stdout.write(self.style.WARNING('\nPara eliminar estos datos de prueba mas tarde:'))
            self.stdout.write('   python manage.py shell')
            self.stdout.write("   >>> from apps.audit.models import AuditLog")
            self.stdout.write(f"   >>> AuditLog.objects.filter(new_values__demo_data=True).delete()")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR: Error al crear registros: {str(e)}'))
            raise

