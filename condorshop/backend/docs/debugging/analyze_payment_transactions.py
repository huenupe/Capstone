"""
Script de análisis exhaustivo de payment_transactions

USO:
    Desde condorshop/backend:
    python manage.py shell < docs/debugging/analyze_payment_transactions.py
    
    O desde docs/debugging:
    cd ../../ && python manage.py shell < docs/debugging/analyze_payment_transactions.py
"""
import os
import sys
import django

# Setup Django - ajustar path para ejecutar desde cualquier ubicación
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop.settings')
django.setup()

from django.db import connection
from apps.orders.models import PaymentTransaction

print("=" * 80)
print("ANÁLISIS EXHAUSTIVO - payment_transactions")
print("=" * 80)

# Detectar tipo de base de datos
db_vendor = connection.vendor
print(f"\nBase de datos detectada: {db_vendor.upper()}")

# ============================================================
# PARTE 1: Estado Actual de la Base de Datos
# ============================================================
print("\n[PARTE 1] COLUMNAS EN BASE DE DATOS")
print("-" * 80)

with connection.cursor() as cursor:
    if db_vendor == 'postgresql':
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'payment_transactions'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        db_columns = {}
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            col_null = col[2]
            col_default = col[3]
            col_max_length = col[4]
            
            # Construir tipo completo
            type_str = col_type
            if col_max_length:
                type_str = f"{col_type}({col_max_length})"
            
            db_columns[col_name] = {
                'type': type_str,
                'null': col_null,
                'key': '',  # PostgreSQL no tiene KEY en esta query
                'default': col_default,
                'extra': ''
            }
            
            print(f"  {col_name:<30} {type_str:<20} NULL:{col_null:<5} DEFAULT:{str(col_default or ''):<10}")
    else:  # MySQL
        cursor.execute("DESCRIBE payment_transactions")
        columns = cursor.fetchall()
        
        db_columns = {}
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            col_null = col[2]
            col_key = col[3]
            col_default = col[4]
            col_extra = col[5]
            
            db_columns[col_name] = {
                'type': col_type,
                'null': col_null,
                'key': col_key,
                'default': col_default,
                'extra': col_extra
            }
            
            print(f"  {col_name:<30} {col_type:<20} NULL:{col_null:<5} KEY:{col_key:<5} DEFAULT:{str(col_default):<10}")

print(f"\nTotal columnas en BD: {len(db_columns)}")

# ============================================================
# PARTE 2: Índices en Base de Datos
# ============================================================
print("\n[PARTE 2] ÍNDICES EN BASE DE DATOS")
print("-" * 80)

with connection.cursor() as cursor:
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
        
        db_indexes = {}
        for idx in indexes:
            idx_name = idx[0]
            idx_def = idx[1]
            # Extraer columnas de la definición
            # Formato típico: CREATE INDEX ... ON ... (column1, column2)
            import re
            cols_match = re.search(r'\(([^)]+)\)', idx_def)
            cols = [c.strip() for c in cols_match.group(1).split(',')] if cols_match else []
            db_indexes[idx_name] = cols
            print(f"  {idx_name:<40} Columnas: {', '.join(cols) if cols else 'N/A'}")
    else:  # MySQL
        cursor.execute("SHOW INDEX FROM payment_transactions")
        indexes = cursor.fetchall()
        
        db_indexes = {}
        for idx in indexes:
            idx_name = idx[2]
            col_name = idx[4]
            if idx_name not in db_indexes:
                db_indexes[idx_name] = []
            db_indexes[idx_name].append(col_name)
        
        for idx_name, cols in db_indexes.items():
            print(f"  {idx_name:<40} Columnas: {', '.join(cols)}")

print(f"\nTotal índices en BD: {len(db_indexes)}")

# ============================================================
# PARTE 3: Foreign Keys en Base de Datos
# ============================================================
print("\n[PARTE 3] FOREIGN KEYS EN BASE DE DATOS")
print("-" * 80)

with connection.cursor() as cursor:
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
    
    for fk in fks:
        print(f"  {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")

# ============================================================
# PARTE 4: Registros en Base de Datos
# ============================================================
print("\n[PARTE 4] REGISTROS EN BASE DE DATOS")
print("-" * 80)

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM payment_transactions")
    count = cursor.fetchone()[0]
    print(f"Total registros: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM payment_transactions LIMIT 1")
        registro = cursor.fetchone()
        
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
        
        print("\nMuestra del primer registro:")
        for i, col_name in enumerate(col_names):
            value = registro[i] if i < len(registro) else None
            # Truncar valores muy largos
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"  {col_name}: {value}")

# ============================================================
# PARTE 5: Campos en Modelo Django
# ============================================================
print("\n[PARTE 5] CAMPOS EN MODELO DJANGO")
print("-" * 80)

model_fields = {}
for field in PaymentTransaction._meta.get_fields():
    field_name = field.name
    field_type = type(field).__name__
    model_fields[field_name] = {
        'type': field_type,
        'db_column': getattr(field, 'db_column', field_name)
    }
    print(f"  {field_name:<30} {field_type:<30} db_column:{getattr(field, 'db_column', field_name)}")

print(f"\nTotal campos en modelo: {len(model_fields)}")

# ============================================================
# PARTE 6: Comparación Modelo vs BD
# ============================================================
print("\n[PARTE 6] COMPARACIÓN: MODELO vs BASE DE DATOS")
print("-" * 80)

# Campos en modelo pero no en BD
model_db_columns = {f.get('db_column', name): name for name, f in model_fields.items()}
missing_in_db = []
for db_col, model_field in model_db_columns.items():
    if db_col not in db_columns and db_col != 'id':
        missing_in_db.append((model_field, db_col))

if missing_in_db:
    print("\n❌ CAMPOS EN MODELO PERO NO EN BD:")
    for model_field, db_col in missing_in_db:
        print(f"  - {model_field} (db_column: {db_col})")
else:
    print("\n✅ Todos los campos del modelo existen en BD")

# Campos en BD pero no en modelo
extra_in_db = []
for db_col in db_columns:
    if db_col not in model_db_columns and db_col != 'id':
        extra_in_db.append(db_col)

if extra_in_db:
    print("\n⚠️  CAMPOS EN BD PERO NO EN MODELO:")
    for db_col in extra_in_db:
        print(f"  - {db_col}")
else:
    print("\n✅ No hay campos extra en BD")

# ============================================================
# PARTE 7: Campos que la migración intenta leer
# ============================================================
print("\n[PARTE 7] CAMPOS QUE LA MIGRACIÓN INTENTA LEER")
print("-" * 80)

fields_to_check = [
    'payment_id', 'payment',  # Campo antiguo
    'tbk_token',  # Campo antiguo
    'buy_order',  # Campo antiguo
    'session_id',  # Campo antiguo
    'authorization_code',  # Campo antiguo
    'response_code',  # Campo antiguo
    'processed_at',  # Campo antiguo
    'card_detail',  # Campo antiguo
    'order_id', 'order',  # Campo nuevo
    'payment_method',  # Campo nuevo
    'currency',  # Campo nuevo
    'webpay_token',  # Campo nuevo
    'webpay_buy_order',  # Campo nuevo
    'webpay_authorization_code',  # Campo nuevo
    'webpay_transaction_date',  # Campo nuevo
    'card_last_four',  # Campo nuevo
    'card_brand',  # Campo nuevo
    'gateway_response',  # Campo nuevo
]

print("\nEstado de campos críticos:")
for field in fields_to_check:
    exists = field in db_columns
    status = "✅ EXISTE" if exists else "❌ NO EXISTE"
    print(f"  {field:<35} {status}")

print("\n" + "=" * 80)
print("ANÁLISIS COMPLETADO")
print("=" * 80)

