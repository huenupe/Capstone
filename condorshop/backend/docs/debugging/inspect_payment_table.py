"""
Script de inspección rápida de payment_transactions

USO:
    Desde condorshop/backend:
    python docs/debugging/inspect_payment_table.py
    
    O desde docs/debugging:
    cd ../../ && python docs/debugging/inspect_payment_table.py
"""
import django
import os
import sys

# Setup Django - ajustar path para ejecutar desde cualquier ubicación
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop.settings')
django.setup()

from django.db import connection

print("=" * 80)
print("ANÁLISIS DE TABLA payment_transactions")
print("=" * 80)

# Detectar tipo de base de datos
db_vendor = connection.vendor
print(f"\nBase de datos detectada: {db_vendor.upper()}")

with connection.cursor() as cursor:
    # 1. Ver estructura completa de la tabla
    if db_vendor == 'postgresql':
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'payment_transactions'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("\n1. COLUMNAS ACTUALES EN LA BD:")
        print("-" * 80)
        for col in columns:
            print(f"  - {col[0]:<30} {col[1]:<20} NULL:{col[2]:<5} DEFAULT:{str(col[3] or ''):<15}")
    else:  # MySQL
        cursor.execute("DESCRIBE payment_transactions")
        columns = cursor.fetchall()
        
        print("\n1. COLUMNAS ACTUALES EN LA BD:")
        print("-" * 80)
        for col in columns:
            print(f"  - {col[0]:<30} {col[1]:<20} NULL:{col[2]:<5} KEY:{col[3]}")
    
    # 2. Ver índices
    if db_vendor == 'postgresql':
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'payment_transactions'
            ORDER BY indexname
        """)
        indexes = cursor.fetchall()
        
        print("\n2. ÍNDICES ACTUALES:")
        print("-" * 80)
        for idx in indexes:
            print(f"  - {idx[0]:<40} Definición: {idx[1][:60]}...")
    else:  # MySQL
        cursor.execute("SHOW INDEX FROM payment_transactions")
        indexes = cursor.fetchall()
        
        print("\n2. ÍNDICES ACTUALES:")
        print("-" * 80)
        seen_indexes = set()
        for idx in indexes:
            idx_name = idx[2]
            if idx_name not in seen_indexes:
                seen_indexes.add(idx_name)
                col_name = idx[4]
                print(f"  - {idx_name:<40} Columna: {col_name}")
    
    # 3. Ver foreign keys
    if db_vendor == 'postgresql':
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'payment_transactions'
        """)
        fks = cursor.fetchall()
    else:  # MySQL
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'payment_transactions'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        fks = cursor.fetchall()
    
    print("\n3. FOREIGN KEYS:")
    print("-" * 80)
    for fk in fks:
        print(f"  - {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")
    
    # 4. Ver cantidad de registros
    cursor.execute("SELECT COUNT(*) FROM payment_transactions")
    count = cursor.fetchone()[0]
    
    print(f"\n4. TOTAL DE REGISTROS: {count}")
    
    # 5. Ver columnas que tienen datos (sample)
    if count > 0:
        cursor.execute("SELECT * FROM payment_transactions LIMIT 1")
        sample = cursor.fetchone()
        
        # Obtener nombres de columnas
        if db_vendor == 'postgresql':
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'payment_transactions'
                ORDER BY ordinal_position
            """)
            col_names = [row[0] for row in cursor.fetchall()]
        else:  # MySQL
            cursor.execute("DESCRIBE payment_transactions")
            col_names = [col[0] for col in cursor.fetchall()]
        
        print("\n5. MUESTRA DE DATOS (primer registro):")
        print("-" * 80)
        for i, col_name in enumerate(col_names):
            value = sample[i] if i < len(sample) else None
            # Truncar valores muy largos
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"  - {col_name}: {value}")

print("\n" + "=" * 80)

