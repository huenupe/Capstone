# Generated manually for refactoring - Acción 2 según plan original
# MIGRACIÓN SEGURA con verificaciones condicionales y SQL directo
from django.db import migrations, models, connection
import django.db.models.deletion


def get_existing_columns(table_name, schema_editor):
    """
    Obtiene lista de columnas que existen en la tabla.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        if db_vendor == 'mysql':
            cursor.execute(f"DESCRIBE {table_name}")
            return [col[0] for col in cursor.fetchall()]
        elif db_vendor == 'postgresql':
            cursor.execute("SELECT current_schema()")
            schema_name = cursor.fetchone()[0]
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = %s
                AND table_name = %s
            """, [schema_name, table_name])
            return [col[0] for col in cursor.fetchall()]
        else:
            # Sintaxis genérica
            cursor.execute(f"DESCRIBE {table_name}")
            return [col[0] for col in cursor.fetchall()]


def column_exists(table_name, column_name, schema_editor):
    """
    Verifica si una columna existe en una tabla.
    Compatible con MySQL y PostgreSQL.
    """
    return column_name in get_existing_columns(table_name, schema_editor)


def index_exists(table_name, index_name, schema_editor):
    """
    Verifica si un índice existe en una tabla.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    
    with schema_editor.connection.cursor() as cursor:
        if db_vendor == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s 
                AND INDEX_NAME = %s
            """, [table_name, index_name])
            return cursor.fetchone()[0] > 0
        elif db_vendor == 'postgresql':
            cursor.execute("SELECT current_schema()")
            schema_name = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = %s
                AND tablename = %s 
                AND indexname = %s
            """, [schema_name, table_name, index_name])
            return cursor.fetchone()[0] > 0
        else:
            return True  # Asumir que existe


def add_column_if_not_exists(table_name, column_name, column_definition, schema_editor):
    """
    Agrega una columna solo si no existe.
    Compatible con MySQL y PostgreSQL.
    """
    if not column_exists(table_name, column_name, schema_editor):
        db_vendor = schema_editor.connection.vendor
        with schema_editor.connection.cursor() as cursor:
            # Ajustar definición según DB
            if db_vendor == 'postgresql':
                # Convertir tipos MySQL a PostgreSQL
                col_def = column_definition.replace('VARCHAR', 'VARCHAR').replace('DATETIME', 'TIMESTAMP')
                # Remover unsigned si existe
                col_def = col_def.replace(' unsigned', '')
            else:
                col_def = column_definition
            
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_def}")
            print(f"  [OK] Agregada columna {column_name}")
    else:
        print(f"  [SKIP] Columna {column_name} ya existe en {table_name}")


def drop_column_if_exists(table_name, column_name, schema_editor):
    """
    Elimina una columna solo si existe.
    Compatible con MySQL y PostgreSQL.
    """
    if column_exists(table_name, column_name, schema_editor):
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
            print(f"  [OK] Eliminada columna {column_name}")
    else:
        print(f"  [SKIP] Columna {column_name} no existe en {table_name}")


def drop_index_if_exists(table_name, index_name, schema_editor):
    """
    Elimina un índice solo si existe.
    Compatible con MySQL y PostgreSQL.
    """
    if index_exists(table_name, index_name, schema_editor):
        db_vendor = schema_editor.connection.vendor
        with schema_editor.connection.cursor() as cursor:
            if db_vendor == 'mysql':
                cursor.execute(f"DROP INDEX {index_name} ON {table_name}")
            elif db_vendor == 'postgresql':
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
            else:
                cursor.execute(f"DROP INDEX {index_name}")
            print(f"  [OK] Eliminado índice {index_name}")
    else:
        print(f"  [SKIP] Índice {index_name} no existe en {table_name}")


def create_index_if_not_exists(table_name, index_name, columns, schema_editor):
    """
    Crea un índice solo si no existe.
    Compatible con MySQL y PostgreSQL.
    """
    if not index_exists(table_name, index_name, schema_editor):
        db_vendor = schema_editor.connection.vendor
        with schema_editor.connection.cursor() as cursor:
            if isinstance(columns, list):
                columns_str = ', '.join(columns)
            else:
                columns_str = columns
            
            if db_vendor == 'postgresql':
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})")
            else:
                cursor.execute(f"CREATE INDEX {index_name} ON {table_name}({columns_str})")
            print(f"  [OK] Creado índice {index_name}")
    else:
        print(f"  [SKIP] Índice {index_name} ya existe en {table_name}")


def add_columns_safely(apps, schema_editor):
    """
    Agrega todas las columnas nuevas de forma segura.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    table_name = 'payment_transactions'
    
    print("\n[PASO 1] Agregando columnas nuevas...")
    
    # Obtener columnas existentes una sola vez
    existing_columns = get_existing_columns(table_name, schema_editor)
    print(f"  [INFO] Columnas existentes: {len(existing_columns)}")
    
    # Campo order_id (FK a Order) - nullable temporalmente
    if 'order_id' not in existing_columns:
        with schema_editor.connection.cursor() as cursor:
            if db_vendor == 'postgresql':
                cursor.execute("""
                    ALTER TABLE payment_transactions 
                    ADD COLUMN order_id BIGINT NULL
                """)
            else:
                cursor.execute("""
                    ALTER TABLE payment_transactions 
                    ADD COLUMN order_id BIGINT NULL
                """)
            # Agregar FK después
            try:
                if db_vendor == 'postgresql':
                    cursor.execute("""
                        ALTER TABLE payment_transactions 
                        ADD CONSTRAINT fk_payment_tx_order 
                        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                    """)
                else:
                    cursor.execute("""
                        ALTER TABLE payment_transactions 
                        ADD CONSTRAINT fk_payment_tx_order 
                        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                    """)
                print("  [OK] Agregada columna order_id con FK")
            except Exception as e:
                print(f"  [WARN] No se pudo agregar FK order_id: {e}")
    else:
        print("  [SKIP] Columna order_id ya existe")
    
    # Resto de campos nuevos
    add_column_if_not_exists(table_name, 'payment_method', "VARCHAR(20) DEFAULT 'webpay'", schema_editor)
    add_column_if_not_exists(table_name, 'currency', "VARCHAR(3) DEFAULT 'CLP'", schema_editor)
    add_column_if_not_exists(table_name, 'webpay_token', "VARCHAR(255) NULL", schema_editor)
    
    # Índice único para webpay_token
    if not index_exists(table_name, 'idx_webpay_token_unique', schema_editor):
        with schema_editor.connection.cursor() as cursor:
            try:
                if db_vendor == 'postgresql':
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_webpay_token_unique 
                        ON payment_transactions(webpay_token)
                    """)
                else:
                    cursor.execute("""
                        CREATE UNIQUE INDEX idx_webpay_token_unique 
                        ON payment_transactions(webpay_token)
                    """)
                print("  [OK] Creado índice único webpay_token")
            except Exception as e:
                print(f"  [WARN] No se pudo crear índice único webpay_token: {e}")
    
    add_column_if_not_exists(table_name, 'webpay_buy_order', "VARCHAR(255) NULL", schema_editor)
    add_column_if_not_exists(table_name, 'webpay_authorization_code', "VARCHAR(50) NULL", schema_editor)
    if db_vendor == 'postgresql':
        add_column_if_not_exists(table_name, 'webpay_transaction_date', "TIMESTAMP NULL", schema_editor)
    else:
        add_column_if_not_exists(table_name, 'webpay_transaction_date', "DATETIME NULL", schema_editor)
    add_column_if_not_exists(table_name, 'card_last_four', "VARCHAR(4) NULL", schema_editor)
    add_column_if_not_exists(table_name, 'card_brand', "VARCHAR(20) NULL", schema_editor)
    add_column_if_not_exists(table_name, 'gateway_response', "JSON NULL", schema_editor)
    
    print("[PASO 1] Completado\n")


def sanitize_payment_data(apps, schema_editor):
    """
    Sanitiza datos de pagos existentes usando SQL directo.
    CRÍTICO: No usa ORM porque el modelo tiene campos que no existen en BD.
    Compatible con MySQL y PostgreSQL.
    """
    print("\n[PASO 2] Migrando datos existentes...")
    
    # Obtener columnas existentes en BD
    existing_columns = get_existing_columns('payment_transactions', schema_editor)
    print(f"  [INFO] Columnas disponibles en BD: {', '.join(existing_columns)}")
    
    # Verificar si hay registros
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM payment_transactions")
        count = cursor.fetchone()[0]
        print(f"  [INFO] Total registros a migrar: {count}")
        
        if count == 0:
            print("  [SKIP] No hay registros para migrar")
            print("[PASO 2] Completado\n")
            return
        
        # Construir SELECT solo con columnas que existen
        select_columns = ['id']  # Siempre existe
        
        # Columnas antiguas (solo si existen)
        old_columns_map = {
            'payment_id': 'payment_id',
            'tbk_token': 'tbk_token',
            'buy_order': 'buy_order',
            'session_id': 'session_id',
            'authorization_code': 'authorization_code',
            'response_code': 'response_code',
            'processed_at': 'processed_at',
            'card_detail': 'card_detail',
            'status': 'status',
            'amount': 'amount',
        }
        
        # Columnas nuevas (solo si existen)
        new_columns_map = {
            'order_id': 'order_id',
            'payment_method': 'payment_method',
            'currency': 'currency',
            'webpay_token': 'webpay_token',
            'webpay_buy_order': 'webpay_buy_order',
            'webpay_authorization_code': 'webpay_authorization_code',
            'webpay_transaction_date': 'webpay_transaction_date',
            'card_last_four': 'card_last_four',
            'card_brand': 'card_brand',
        }
        
        # Agregar columnas que existen
        for col in old_columns_map.keys():
            if col in existing_columns:
                select_columns.append(col)
        
        for col in new_columns_map.keys():
            if col in existing_columns:
                select_columns.append(col)
        
        print(f"  [INFO] Columnas a leer: {', '.join(select_columns)}")
        
        # Leer todos los registros
        cursor.execute(f"SELECT {', '.join(select_columns)} FROM payment_transactions")
        rows = cursor.fetchall()
        
        print(f"  [INFO] Procesando {len(rows)} registros...")
        
        # Crear diccionario de índices de columnas
        col_indices = {col: i for i, col in enumerate(select_columns)}
        
        updates_count = 0
        
        for row in rows:
            row_id = row[col_indices['id']]
            updates = {}
            
            # 1. Migrar order_id desde payment_id si existe
            if 'payment_id' in col_indices and row[col_indices['payment_id']]:
                if 'order_id' in col_indices:
                    # Obtener order_id desde payment
                    payment_id = row[col_indices['payment_id']]
                    cursor.execute("""
                        SELECT order_id FROM payments WHERE id = %s
                    """, [payment_id])
                    payment_result = cursor.fetchone()
                    if payment_result and payment_result[0]:
                        order_id = payment_result[0]
                        if 'order_id' not in col_indices or not row[col_indices.get('order_id')]:
                            updates['order_id'] = order_id
            
            # 2. Migrar card_detail a card_last_four
            if 'card_detail' in col_indices and row[col_indices['card_detail']]:
                if 'card_last_four' in col_indices:
                    card_str = str(row[col_indices['card_detail']]).replace(' ', '').replace('-', '')
                    digits = ''.join(filter(str.isdigit, card_str))
                    if len(digits) >= 4:
                        card_last_four = digits[-4:]
                        if not row[col_indices.get('card_last_four')]:
                            updates['card_last_four'] = card_last_four
            
            # 3. Migrar tbk_token a webpay_token
            if 'tbk_token' in col_indices and row[col_indices['tbk_token']]:
                if 'webpay_token' in col_indices:
                    tbk_token = row[col_indices['tbk_token']]
                    if not row[col_indices.get('webpay_token')]:
                        updates['webpay_token'] = tbk_token
            
            # 4. Migrar buy_order a webpay_buy_order
            if 'buy_order' in col_indices and row[col_indices['buy_order']]:
                if 'webpay_buy_order' in col_indices:
                    buy_order = row[col_indices['buy_order']]
                    if not row[col_indices.get('webpay_buy_order')]:
                        updates['webpay_buy_order'] = buy_order
            
            # 5. Migrar authorization_code a webpay_authorization_code
            if 'authorization_code' in col_indices and row[col_indices['authorization_code']]:
                if 'webpay_authorization_code' in col_indices:
                    auth_code = row[col_indices['authorization_code']]
                    if not row[col_indices.get('webpay_authorization_code')]:
                        updates['webpay_authorization_code'] = auth_code
            
            # 6. Migrar processed_at a webpay_transaction_date
            if 'processed_at' in col_indices and row[col_indices['processed_at']]:
                if 'webpay_transaction_date' in col_indices:
                    processed_at = row[col_indices['processed_at']]
                    if not row[col_indices.get('webpay_transaction_date')]:
                        updates['webpay_transaction_date'] = processed_at
            
            # 7. Asegurar payment_method tiene valor
            if 'payment_method' in col_indices:
                if not row[col_indices.get('payment_method')]:
                    updates['payment_method'] = 'webpay'
            
            # 8. Asegurar currency tiene valor
            if 'currency' in col_indices:
                if not row[col_indices.get('currency')]:
                    updates['currency'] = 'CLP'
            
            # 9. Mapear status si es necesario
            if 'status' in col_indices and row[col_indices['status']]:
                old_status = str(row[col_indices['status']]).lower()
                if old_status in ['approved', 'completed', 'success']:
                    new_status = 'approved'
                elif old_status in ['rejected', 'declined']:
                    new_status = 'rejected'
                elif old_status in ['failed', 'error']:
                    new_status = 'failed'
                elif old_status in ['cancelled', 'canceled']:
                    new_status = 'cancelled'
                elif old_status == 'pending':
                    new_status = 'pending'
                else:
                    new_status = 'pending'
                
                if old_status != new_status:
                    updates['status'] = new_status
            
            # Ejecutar UPDATE si hay cambios
            if updates:
                set_clauses = []
                values = []
                for col, val in updates.items():
                    set_clauses.append(f"{col} = %s")
                    values.append(val)
                
                values.append(row_id)  # Para el WHERE
                
                update_sql = f"""
                    UPDATE payment_transactions 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                
                try:
                    cursor.execute(update_sql, values)
                    updates_count += 1
                except Exception as e:
                    print(f"  [ERROR] Error actualizando registro {row_id}: {e}")
        
        print(f"  [OK] Actualizados {updates_count} registros")
        print("[PASO 2] Completado\n")


def make_order_required(apps, schema_editor):
    """
    Hace order_id obligatorio después de migrar datos.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    print("\n[PASO 3] Haciendo order_id obligatorio...")
    
    if not column_exists('payment_transactions', 'order_id', schema_editor):
        print("  [SKIP] order_id no existe, no se puede hacer obligatorio")
        print("[PASO 3] Completado\n")
        return
    
    # Primero actualizar NULLs si los hay (desde payment_id si existe)
    if column_exists('payment_transactions', 'payment_id', schema_editor):
        with schema_editor.connection.cursor() as cursor:
            try:
                if db_vendor == 'postgresql':
                    cursor.execute("""
                        UPDATE payment_transactions pt
                        SET order_id = p.order_id
                        FROM payments p
                        WHERE pt.payment_id = p.id
                        AND pt.order_id IS NULL
                    """)
                else:
                    cursor.execute("""
                        UPDATE payment_transactions pt
                        INNER JOIN payments p ON pt.payment_id = p.id
                        SET pt.order_id = p.order_id
                        WHERE pt.order_id IS NULL
                    """)
                updated = cursor.rowcount
                if updated > 0:
                    print(f"  [OK] Actualizados {updated} registros con order_id desde payment")
            except Exception as e:
                print(f"  [WARN] No se pudo actualizar order_id desde payment: {e}")
    
    # Verificar si quedan NULLs
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM payment_transactions WHERE order_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"  [WARN] Quedan {null_count} registros con order_id NULL")
            print("  [INFO] No se puede hacer NOT NULL, manteniendo nullable")
        else:
            # Luego hacer NOT NULL (sintaxis diferente por DB)
            with schema_editor.connection.cursor() as cursor:
                try:
                    if db_vendor == 'mysql':
                        cursor.execute("ALTER TABLE payment_transactions MODIFY COLUMN order_id BIGINT NOT NULL")
                    elif db_vendor == 'postgresql':
                        cursor.execute("ALTER TABLE payment_transactions ALTER COLUMN order_id SET NOT NULL")
                    else:
                        cursor.execute("ALTER TABLE payment_transactions ALTER COLUMN order_id SET NOT NULL")
                    print("  [OK] order_id ahora es NOT NULL")
                except Exception as e:
                    print(f"  [WARN] No se pudo hacer order_id NOT NULL: {e}")
    
    print("[PASO 3] Completado\n")


def remove_old_fields_safely(apps, schema_editor):
    """
    Elimina campos antiguos de forma segura.
    Compatible con MySQL y PostgreSQL.
    """
    db_vendor = schema_editor.connection.vendor
    table_name = 'payment_transactions'
    
    print("\n[PASO 4] Eliminando campos antiguos...")
    
    # Eliminar índices antiguos primero
    drop_index_if_exists(table_name, 'idx_payment_tx_session', schema_editor)
    drop_index_if_exists(table_name, 'idx_payment_tx_token', schema_editor)
    drop_index_if_exists(table_name, 'idx_payment_tx_buy_order', schema_editor)
    
    # Eliminar campos
    drop_column_if_exists(table_name, 'card_detail', schema_editor)
    
    # Eliminar FK de payment_id antes de eliminar la columna (solo MySQL)
    if db_vendor == 'mysql' and column_exists(table_name, 'payment_id', schema_editor):
        with schema_editor.connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'payment_transactions' 
                    AND COLUMN_NAME = 'payment_id' 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                fk_result = cursor.fetchone()
                if fk_result:
                    fk_name = fk_result[0]
                    cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk_name}")
                    print(f"  [OK] Eliminada FK {fk_name}")
            except Exception as e:
                print(f"  [WARN] No se pudo eliminar FK de payment_id: {e}")
    elif db_vendor == 'postgresql' and column_exists(table_name, 'payment_id', schema_editor):
        # En PostgreSQL, las FKs se eliminan automáticamente al eliminar la columna
        # Pero podemos intentar eliminarla explícitamente primero
        with schema_editor.connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'payment_transactions' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%payment_id%'
                """)
                fk_result = cursor.fetchone()
                if fk_result:
                    fk_name = fk_result[0]
                    cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {fk_name}")
                    print(f"  [OK] Eliminada constraint {fk_name} (si existía)")
            except Exception as e:
                print(f"  [WARN] No se pudo eliminar constraint de payment_id: {e}")
    
    drop_column_if_exists(table_name, 'payment_id', schema_editor)
    drop_column_if_exists(table_name, 'tbk_token', schema_editor)
    drop_column_if_exists(table_name, 'buy_order', schema_editor)
    drop_column_if_exists(table_name, 'session_id', schema_editor)
    drop_column_if_exists(table_name, 'authorization_code', schema_editor)
    drop_column_if_exists(table_name, 'response_code', schema_editor)
    drop_column_if_exists(table_name, 'processed_at', schema_editor)
    
    print("[PASO 4] Completado\n")


def create_new_indexes_safely(apps, schema_editor):
    """
    Crea nuevos índices de forma segura.
    Compatible con MySQL y PostgreSQL.
    """
    table_name = 'payment_transactions'
    
    print("\n[PASO 5] Creando nuevos índices...")
    
    # Verificar que las columnas existen antes de crear índices
    existing_columns = get_existing_columns(table_name, schema_editor)
    
    if 'order_id' in existing_columns:
        create_index_if_not_exists(table_name, 'idx_payment_tx_order', 'order_id', schema_editor)
    else:
        print("  [SKIP] order_id no existe, no se puede crear índice")
    
    if 'status' in existing_columns:
        create_index_if_not_exists(table_name, 'idx_payment_tx_status', 'status', schema_editor)
    else:
        print("  [SKIP] status no existe, no se puede crear índice")
    
    if 'webpay_token' in existing_columns:
        create_index_if_not_exists(table_name, 'idx_payment_webpay_token', 'webpay_token', schema_editor)
    else:
        print("  [SKIP] webpay_token no existe, no se puede crear índice")
    
    if 'created_at' in existing_columns:
        create_index_if_not_exists(table_name, 'idx_payment_tx_created', 'created_at', schema_editor)
    else:
        print("  [SKIP] created_at no existe, no se puede crear índice")
    
    print("[PASO 5] Completado\n")


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_remove_payment_amount_field'),
    ]

    operations = [
        # Paso 1: Agregar columnas nuevas
        migrations.RunPython(
            add_columns_safely,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Paso 2: Migrar datos usando SQL directo
        migrations.RunPython(
            sanitize_payment_data,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Paso 3: Hacer order_id obligatorio
        migrations.RunPython(
            make_order_required,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Paso 4: Actualizar status a choices (usando AlterField de Django)
        migrations.AlterField(
            model_name='paymenttransaction',
            name='status',
            field=models.CharField(
                default='pending',
                max_length=20,
                db_column='status',
                choices=[
                    ('pending', 'Pendiente'),
                    ('approved', 'Aprobado'),
                    ('rejected', 'Rechazado'),
                    ('failed', 'Fallido'),
                    ('cancelled', 'Cancelado'),
                ],
                verbose_name='Estado'
            ),
        ),
        
        # Paso 5: Eliminar campos antiguos
        migrations.RunPython(
            remove_old_fields_safely,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Paso 6: Crear nuevos índices
        migrations.RunPython(
            create_new_indexes_safely,
            reverse_code=migrations.RunPython.noop
        ),
    ]
