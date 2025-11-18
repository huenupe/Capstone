"""
Comando de gestión para limpiar datos corruptos en payment_transactions.

Este comando corrige registros donde gateway_response está almacenado como
diccionario Python en lugar de JSON string, lo cual puede causar problemas
de serialización y consultas.
"""

import json
import logging
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.orders.models import PaymentTransaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia datos corruptos en payment_transactions.gateway_response convirtiendo diccionarios Python a JSON string'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin hacer cambios reales',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limitar número de registros a procesar (útil para pruebas)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')

        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Limpieza de datos corruptos en payment_transactions'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO SIMULACIÓN: No se realizarán cambios reales\n'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ MODO REAL: Se aplicarán cambios a la base de datos\n'))

        # Contar registros totales con gateway_response
        total_count = PaymentTransaction.objects.filter(
            gateway_response__isnull=False
        ).count()
        
        self.stdout.write(f'Total de registros con gateway_response: {total_count}')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No hay registros para procesar.'))
            return

        # Usar SQL directo porque el ORM puede fallar si hay datos corruptos
        # (dict almacenado en lugar de JSON string)
        corrected_count = 0
        error_count = 0
        skipped_count = 0

        # Obtener registros usando SQL directo para evitar errores de deserialización
        with connection.cursor() as cursor:
            query = """
                SELECT id, gateway_response 
                FROM payment_transactions 
                WHERE gateway_response IS NOT NULL
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()

        total_to_process = len(rows)
        self.stdout.write(f'\nProcesando {total_to_process} registros...\n')

        for row_id, gateway_response_raw in rows:
            try:
                # gateway_response_raw viene directamente de la BD (puede ser string JSON o dict corrupto)
                if gateway_response_raw is None:
                    skipped_count += 1
                    continue

                # Detectar el tipo y si necesita corrección
                needs_correction = False
                normalized_value = None
                
                # Caso 1: Es un diccionario Python (CORRUPTO - debe ser JSON string)
                if isinstance(gateway_response_raw, dict):
                    # Este es el problema: está almacenado como dict en lugar de JSON string
                    needs_correction = True
                    normalized_value = gateway_response_raw
                
                # Caso 2: Es una lista Python (CORRUPTO - debe ser JSON string)
                elif isinstance(gateway_response_raw, list):
                    needs_correction = True
                    normalized_value = gateway_response_raw
                
                # Caso 3: Es un string (puede ser JSON válido o corrupto)
                elif isinstance(gateway_response_raw, str):
                    try:
                        # Intentar parsear para validar que es JSON válido
                        parsed = json.loads(gateway_response_raw)
                        # Si es JSON válido, está bien almacenado
                        # Pero podemos normalizarlo guardándolo de nuevo para asegurar consistencia
                        needs_correction = True  # Normalizar para asegurar formato consistente
                        normalized_value = parsed
                    except (json.JSONDecodeError, TypeError) as e:
                        # String inválido (no es JSON válido) - necesita corrección
                        needs_correction = True
                        error_msg = f'String JSON inválido en registro {row_id}: {str(e)[:100]}'
                        self.stdout.write(self.style.WARNING(f'⚠ {error_msg}'))
                        logger.warning(error_msg)
                        normalized_value = {}  # Fallback: dict vacío
                
                # Caso 4: Otro tipo
                else:
                    needs_correction = True
                    normalized_value = {}

                if needs_correction:
                    # Convertir a JSON string para guardarlo correctamente
                    json_string = json.dumps(normalized_value, ensure_ascii=False, default=str)
                    
                    if not dry_run:
                        # Actualizar usando SQL directo (más seguro para datos corruptos)
                        # PostgreSQL acepta JSON string y lo convierte automáticamente a JSONB
                        with connection.cursor() as update_cursor:
                            with transaction.atomic():
                                # Usar jsonb_set o simplemente asignar el JSON string
                                # PostgreSQL convertirá automáticamente el string JSON a JSONB
                                update_cursor.execute(
                                    "UPDATE payment_transactions SET gateway_response = %s::jsonb WHERE id = %s",
                                    [json_string, row_id]
                                )
                    
                    corrected_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Corregido registro {row_id}')
                    )
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                error_msg = f'✗ Error procesando registro {row_id}: {str(e)}'
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(f'Error en clean_payment_transactions para registro {row_id}: {e}', exc_info=True)

        # Resumen final
        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('RESUMEN'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(f'Total procesado: {total_to_process}')
        self.stdout.write(self.style.SUCCESS(f'Registros corregidos: {corrected_count}'))
        self.stdout.write(f'Registros sin cambios: {skipped_count}')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errores encontrados: {error_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO SIMULACIÓN: No se aplicaron cambios reales'))
            self.stdout.write(self.style.WARNING('Ejecuta sin --dry-run para aplicar los cambios'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Limpieza completada exitosamente'))

