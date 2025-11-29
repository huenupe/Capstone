"""
Comando para optimizar índices de base de datos PostgreSQL.

Este comando crea índices adicionales recomendados para mejorar el rendimiento
de queries críticas identificadas en la auditoría de base de datos.

Índices a crear:
1. GIN index para búsqueda de texto en nombres de productos (pg_trgm)
2. Índice compuesto para filtros de productos activos (active, category, price)
3. Índice parcial para carritos activos de usuarios autenticados
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega índices de optimización a la base de datos PostgreSQL'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🚀 Optimizando índices de base de datos...\n'))
        
        with connection.cursor() as cursor:
            # Habilitar extensión pg_trgm si no está habilitada (requerida para búsqueda GIN)
            extension_query = "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
            
            try:
                cursor.execute(extension_query)
                self.stdout.write(self.style.SUCCESS('✅ Extensión pg_trgm verificada/creada'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Advertencia con extensión pg_trgm: {e}'))
                self.stdout.write(self.style.WARNING('   El índice GIN puede fallar sin esta extensión'))
            
            # Definir los índices a crear
            indexes = [
                {
                    'name': 'idx_product_name_trgm',
                    'table': 'products',
                    'query': '''
                        CREATE INDEX IF NOT EXISTS idx_product_name_trgm 
                        ON products USING gin (name gin_trgm_ops);
                    ''',
                    'description': 'Índice GIN para búsqueda de texto en nombres de productos (optimiza ILIKE, LIKE)'
                },
                {
                    'name': 'idx_product_active_category_price',
                    'table': 'products',
                    'query': '''
                        CREATE INDEX IF NOT EXISTS idx_product_active_category_price 
                        ON products (active, category_id, price) 
                        WHERE active = true;
                    ''',
                    'description': 'Índice compuesto parcial para productos activos filtrados por categoría y precio'
                },
                {
                    'name': 'idx_cart_active_user',
                    'table': 'carts',
                    'query': '''
                        CREATE INDEX IF NOT EXISTS idx_cart_active_user 
                        ON carts (user_id, created_at) 
                        WHERE is_active = true AND user_id IS NOT NULL;
                    ''',
                    'description': 'Índice parcial para carritos activos de usuarios autenticados'
                }
            ]
            
            created_count = 0
            failed_count = 0
            
            for idx in indexes:
                try:
                    self.stdout.write(f'\n📊 Creando índice: {idx["name"]}')
                    self.stdout.write(f'   {idx["description"]}')
                    
                    cursor.execute(idx['query'])
                    created_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Índice {idx["name"]} creado exitosamente'))
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e).split('\n')[0]  # Mostrar solo primera línea del error
                    self.stdout.write(self.style.ERROR(f'   ❌ Error creando índice {idx["name"]}: {error_msg}'))
                    
                    # Si el índice ya existe, no es un error crítico
                    if 'already exists' in error_msg.lower():
                        self.stdout.write(self.style.WARNING('   ℹ️  El índice ya existe, omitiendo...'))
                        failed_count -= 1
                        created_count += 1
            
            # Resumen final
            self.stdout.write(self.style.MIGRATE_HEADING(f'\n📈 Resumen:'))
            self.stdout.write(self.style.SUCCESS(f'   ✅ Índices creados/existentes: {created_count}'))
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f'   ❌ Índices con errores: {failed_count}'))
            
            # Verificar tamaño de índices creados
            self.stdout.write(self.style.MIGRATE_HEADING('\n💾 Tamaño de índices optimizados:'))
            try:
                size_query = '''
                    SELECT 
                        indexname,
                        pg_size_pretty(pg_relation_size(indexname::regclass)) AS size
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                        AND indexname IN (
                            'idx_product_name_trgm',
                            'idx_product_active_category_price',
                            'idx_cart_active_user'
                        )
                    ORDER BY indexname;
                '''
                cursor.execute(size_query)
                results = cursor.fetchall()
                
                if results:
                    for indexname, size in results:
                        self.stdout.write(f'   {indexname}: {size}')
                else:
                    self.stdout.write(self.style.WARNING('   ℹ️  No se encontraron índices nuevos'))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo obtener tamaño de índices: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n✨ Optimización de índices completada!'))
            self.stdout.write(self.style.MIGRATE_HEADING('\n💡 Próximos pasos:'))
            self.stdout.write('   1. Ejecutar ANALYZE en las tablas: ANALYZE products; ANALYZE carts;')
            self.stdout.write('   2. Verificar uso de índices con: python manage.py analyze_indexes')
            self.stdout.write('   3. Monitorear rendimiento de queries después de aplicar índices\n')

