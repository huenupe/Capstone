"""
Comando de management para diagnosticar queries del Django Admin.

⚠️ IMPORTANTE: Este comando es SOLO para entornos de desarrollo/debugging.
NO afecta a producción ni debe ejecutarse en entornos productivos.

Uso:
    python manage.py debug_admin_queries

Analiza las queries ejecutadas en las páginas del admin de pagos y transacciones.
"""

from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings
from django.db import connection, reset_queries
from django.contrib.auth import get_user_model
from collections import Counter
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnostica queries del Django Admin para pagos y transacciones (solo desarrollo)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL específica a analizar (ej: /admin/orders/payment/)',
            default=None
        )

    def handle(self, *args, **options):
        # ⚠️ Solo ejecutar en desarrollo
        from django.conf import settings
        if not settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Este comando solo debe ejecutarse en entornos de desarrollo (DEBUG=True).'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('🔍 Analizando queries del Django Admin...\n'))

        # Crear cliente de prueba
        client = Client()

        # Obtener o crear usuario de prueba para autenticación
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('❌ No hay usuarios en la base de datos. Crea uno primero.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al obtener usuario: {e}')
            )
            return

        # Autenticar cliente
        client.force_login(user)

        # URLs a analizar
        urls_to_analyze = []
        if options['url']:
            urls_to_analyze = [options['url']]
        else:
            urls_to_analyze = [
                '/admin/orders/payment/',
                '/admin/orders/paymenttransaction/',
            ]

        for url in urls_to_analyze:
            self.stdout.write(self.style.HTTP_INFO(f'\n📊 Analizando: {url}'))
            self.stdout.write('=' * 80)

            # Limpiar queries anteriores
            reset_queries()
            connection.queries_log.clear()

            try:
                # Realizar petición
                response = client.get(url, HTTP_HOST='localhost')

                if response.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error {response.status_code} al acceder a {url}')
                    )
                    continue

                # Analizar queries
                queries = connection.queries
                total_queries = len(queries)
                total_time = sum(float(q['time']) for q in queries)

                self.stdout.write(f'\n📈 Resumen:')
                self.stdout.write(f'   Total de queries: {total_queries}')
                self.stdout.write(f'   Tiempo total: {total_time:.3f}s')
                self.stdout.write(f'   Tiempo promedio por query: {total_time/total_queries:.3f}s' if total_queries > 0 else '   N/A')

                # Normalizar y agrupar queries similares
                self.stdout.write(f'\n🔍 Análisis de queries repetidas:')
                normalized_queries = []
                for q in queries:
                    # Normalizar SQL: reemplazar valores específicos por placeholders
                    sql = q['sql']
                    # Reemplazar IDs específicos
                    sql = re.sub(r'\b\d+\b', '?', sql)
                    # Reemplazar strings específicos
                    sql = re.sub(r"'[^']*'", "'?'", sql)
                    # Normalizar espacios
                    sql = ' '.join(sql.split())
                    normalized_queries.append(sql)

                # Contar repeticiones
                query_counts = Counter(normalized_queries)
                repeated_queries = {sql: count for sql, count in query_counts.items() if count > 1}

                if repeated_queries:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠️  Se encontraron {len(repeated_queries)} patrones de queries repetidas:'
                    ))
                    for sql, count in sorted(repeated_queries.items(), key=lambda x: x[1], reverse=True)[:10]:
                        # Truncar SQL largo para legibilidad
                        sql_short = sql[:100] + '...' if len(sql) > 100 else sql
                        self.stdout.write(f'      [{count}x] {sql_short}')
                    
                    if len(repeated_queries) > 10:
                        self.stdout.write(f'      ... y {len(repeated_queries) - 10} patrones más')
                else:
                    self.stdout.write(self.style.SUCCESS('   ✅ No se detectaron queries repetidas (N+1)'))

                # Mostrar queries más lentas
                slow_queries = sorted(queries, key=lambda q: float(q['time']), reverse=True)[:5]
                if slow_queries:
                    self.stdout.write(f'\n⏱️  Top 5 queries más lentas:')
                    for i, q in enumerate(slow_queries, 1):
                        sql_short = q['sql'][:80] + '...' if len(q['sql']) > 80 else q['sql']
                        self.stdout.write(f'   {i}. [{q["time"]}s] {sql_short}')

                # Detectar posibles N+1
                if total_queries > 20:
                    self.stdout.write(self.style.WARNING(
                        f'\n⚠️  ADVERTENCIA: Se ejecutaron {total_queries} queries. '
                        f'Esto podría indicar problemas de N+1.'
                    ))
                elif total_queries < 10:
                    self.stdout.write(self.style.SUCCESS(
                        f'\n✅ EXCELENTE: Solo {total_queries} queries ejecutadas.'
                    ))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al analizar {url}: {e}')
                )
                import traceback
                self.stdout.write(traceback.format_exc())

        self.stdout.write(self.style.SUCCESS('\n✅ Análisis completado.\n'))

