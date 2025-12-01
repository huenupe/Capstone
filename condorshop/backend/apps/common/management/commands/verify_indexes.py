"""
Comando para verificar que los índices opcionales se crearon correctamente.

Ejecutar: python manage.py verify_indexes
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica que los índices opcionales se crearon correctamente'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('VERIFICACION DE INDICES OPCIONALES'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        db_vendor = connection.vendor
        self.stdout.write(f'\nBase de datos: {db_vendor}\n')
        
        with connection.cursor() as cursor:
            # 1. Verificar índice GIN de products.description
            self.stdout.write('1. Verificando indice GIN para products.description...')
            if db_vendor == 'postgresql':
                cursor.execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'products' 
                    AND indexname = 'idx_product_description_trgm'
                """)
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS(f'   OK: Indice encontrado: {result[0]}'))
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice idx_product_description_trgm NO encontrado'))
            else:
                self.stdout.write(self.style.WARNING('   INFO: Indice GIN solo disponible en PostgreSQL'))
            
            # 2. Verificar índice parcial de carts.session_token
            self.stdout.write('\n2. Verificando indice parcial para carts.session_token...')
            if db_vendor == 'postgresql':
                cursor.execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'carts' 
                    AND indexname = 'idx_cart_active_session'
                """)
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS(f'   OK: Indice encontrado: {result[0]}'))
                    self.stdout.write(f'   Definicion: {result[1][:80]}...')
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice idx_cart_active_session NO encontrado'))
            else:
                self.stdout.write(self.style.WARNING('   INFO: Indice parcial solo disponible en PostgreSQL'))
            
            # 3. Verificar índice compuesto de hero_carousel_slides
            self.stdout.write('\n3. Verificando indice compuesto para hero_carousel_slides...')
            if db_vendor == 'postgresql':
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'hero_carousel_slides' 
                    AND indexname = 'idx_hero_slide_active_order_created'
                """)
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS(f'   OK: Indice encontrado: {result[0]}'))
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice idx_hero_slide_active_order_created NO encontrado'))
            elif db_vendor == 'mysql':
                cursor.execute("SHOW INDEX FROM hero_carousel_slides WHERE Key_name = 'idx_hero_slide_active_order_created'")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS('   OK: Indice encontrado en MySQL'))
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice NO encontrado en MySQL'))
            else:
                self.stdout.write(self.style.WARNING('   ADVERTENCIA: No se puede verificar en esta base de datos'))
            
            # 4. Verificar índice compuesto de payment_transactions
            self.stdout.write('\n4. Verificando indice compuesto para payment_transactions...')
            if db_vendor == 'postgresql':
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'payment_transactions' 
                    AND indexname = 'idx_payment_tx_order_status'
                """)
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS(f'   OK: Indice encontrado: {result[0]}'))
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice idx_payment_tx_order_status NO encontrado'))
            elif db_vendor == 'mysql':
                cursor.execute("SHOW INDEX FROM payment_transactions WHERE Key_name = 'idx_payment_tx_order_status'")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS('   OK: Indice encontrado en MySQL'))
                else:
                    self.stdout.write(self.style.WARNING('   ADVERTENCIA: Indice NO encontrado en MySQL'))
            else:
                self.stdout.write(self.style.WARNING('   ADVERTENCIA: No se puede verificar en esta base de datos'))

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Verificacion completada'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60 + '\n'))

