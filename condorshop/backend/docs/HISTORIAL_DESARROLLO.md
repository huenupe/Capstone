# 📚 Historial de Desarrollo - CondorShop

**Última actualización:** Noviembre 2025  
**Estado:** Documentación histórica consolidada

---

## 📋 Índice

1. [Correcciones de Timezone en Admin de Auditoría](#1-correcciones-de-timezone-en-admin-de-auditoría)
2. [Migración 0008: Refactor de Payment Transactions Webpay](#2-migración-0008-refactor-de-payment-transactions-webpay)
3. [Acción 8: Índices de Performance](#3-acción-8-índices-de-performance)
4. [Acción 9: Constraints y Validaciones](#4-acción-9-constraints-y-validaciones)
5. [Acción 10: Tabla de Configuración (StoreConfig)](#5-acción-10-tabla-de-configuración-storeconfig)
6. [Verificación del Plan Original de Refactorización](#6-verificación-del-plan-original-de-refactorización)
7. [Scripts de Debugging](#7-scripts-de-debugging)

---

## 1. Correcciones de Timezone en Admin de Auditoría

**Fecha:** 2025-11-15  
**Problema:** `ValueError: Database returned an invalid datetime value. Are time zone definitions for your database installed?`

### Problema Identificado

El error ocurría al acceder a `/admin/audit/auditlog/` debido a:

1. **`date_hierarchy = 'created_at'`**: Django intenta generar una jerarquía de fechas que requiere timezone tables en MySQL
2. **Uso de `created_at__date`**: El filtro `__date` puede causar problemas con timezones en MySQL
3. **Falta de manejo de errores**: Si fallaba una query, todo el admin fallaba

### Correcciones Aplicadas

#### 1. Removido `date_hierarchy`

**Razón**: `date_hierarchy` requiere que MySQL tenga las timezone tables instaladas. Se puede reactivar después de instalar:
```sql
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
```

#### 2. Mejorado manejo de fechas en `changelist_view`

**Antes:**
```python
date = (timezone.now() - timedelta(days=6-i)).date()
count = AuditLog.objects.filter(created_at__date=date).count()
```

**Después:**
```python
target_date = timezone.now() - timedelta(days=6-i)
count = AuditLog.objects.filter(
    created_at__gte=target_date.replace(hour=0, minute=0, second=0, microsecond=0),
    created_at__lt=(target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
).count()
```

**Razón**: Usar `__date` puede causar problemas con timezones. Usar rangos de fecha es más robusto.

#### 3. Agregado manejo de errores

Si hay un error en las queries, el admin sigue funcionando mostrando valores por defecto.

### Estado Final

- ✅ **Problema resuelto**: El admin funciona correctamente
- ✅ **Sin errores**: Todas las verificaciones pasaron
- ✅ **Robusto**: Manejo de errores implementado
- ✅ **Compatible**: Funciona con MySQL sin timezone tables

---

## 2. Migración 0008: Refactor de Payment Transactions Webpay

**Fecha:** 2025-11-14  
**Migración:** `orders.0008_refactor_payment_transactions_webpay`

### Estado Actual

#### Migraciones Aplicadas
```
orders
 [X] 0001_initial
 [X] 0002_initial
 [X] 0003_rename_idx_token_idx_payment_tx_token_and_more
 [X] 0004_alter_payment_amount
 [X] 0005_create_shipping_snapshots
 [X] 0006_create_item_snapshots
 [X] 0007_remove_payment_amount_field
 [X] 0008_refactor_payment_transactions_webpay  ← APLICADA
```

### Cambios Realizados

#### Campos Nuevos Agregados
- `order` (FK a Order) - Reemplaza `payment`
- `payment_method` - Método de pago (default: 'webpay')
- `currency` - Moneda (default: 'CLP')
- `webpay_token` - Token de Webpay (único)
- `webpay_buy_order` - Buy order de Webpay
- `webpay_authorization_code` - Código de autorización
- `webpay_transaction_date` - Fecha de transacción
- `card_last_four` - Últimos 4 dígitos de tarjeta
- `card_brand` - Marca de tarjeta
- `gateway_response` - Respuesta completa del gateway (JSON)

#### Campos Eliminados
- ❌ `payment` (FK) → Reemplazado por `order`
- ❌ `card_detail` → Reemplazado por `card_last_four` + `card_brand`
- ❌ `tbk_token` → Reemplazado por `webpay_token`
- ❌ `buy_order` → Reemplazado por `webpay_buy_order`
- ❌ `session_id` → Eliminado (no necesario)
- ❌ `authorization_code` → Reemplazado por `webpay_authorization_code`
- ❌ `response_code` → Eliminado (no necesario)
- ❌ `processed_at` → Reemplazado por `webpay_transaction_date`

#### Índices Nuevos
- ✅ `idx_payment_tx_order` (en `order_id`)
- ✅ `idx_payment_tx_status` (en `status`)
- ✅ `idx_payment_webpay_token` (en `webpay_token`)
- ✅ `idx_payment_tx_created` (en `created_at`)

#### Índices Eliminados
- ❌ `idx_payment_tx_session` (basado en `session_id`)
- ❌ `idx_payment_tx_token` (basado en `tbk_token`)
- ❌ `idx_payment_tx_buy_order` (basado en `buy_order`)

### Solución Implementada

#### Características de Seguridad

1. **Verificaciones Condicionales**: Todas las operaciones verifican existencia antes de ejecutar
2. **SQL Directo**: No usa ORM para evitar problemas de sincronización modelo-BD
3. **Idempotente**: Puede ejecutarse múltiples veces sin errores
4. **Logging**: Mensajes informativos durante la ejecución

#### Estructura de la Migración

```python
operations = [
    # PASO 1: Agregar columnas nuevas (verificando existencia)
    RunPython(add_columns_safely),
    
    # PASO 2: Migrar datos existentes
    RunPython(sanitize_payment_data),
    
    # PASO 3: Hacer order_id obligatorio
    RunPython(make_order_required),
    
    # PASO 4: Actualizar status a choices
    AlterField(status),
    
    # PASO 5: Eliminar campos antiguos (verificando existencia)
    RunPython(remove_old_fields_safely),
    
    # PASO 6: Crear nuevos índices (verificando existencia)
    RunPython(create_new_indexes_safely),
]
```

### Resumen de Cambios

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Relación** | `payment` (FK a Payment) | `order` (FK a Order) |
| **Datos de Tarjeta** | `card_detail` (completo) | `card_last_four` + `card_brand` (solo últimos 4) |
| **Campos Webpay** | `tbk_token`, `buy_order`, `authorization_code` | `webpay_token`, `webpay_buy_order`, `webpay_authorization_code` |
| **Método de Pago** | No existía | `payment_method` con choices |
| **Moneda** | No existía | `currency` (default 'CLP') |
| **Respuesta Gateway** | No existía | `gateway_response` (JSON) |
| **Índices** | 3 índices antiguos | 4 índices nuevos optimizados |

---

## 3. Acción 8: Índices de Performance

**Fecha:** 2025-11-15  
**Estado:** ✅ COMPLETADO Y VERIFICADO

### Migración Aplicada

- ✅ Migración `0010_add_performance_indexes` aplicada exitosamente
- ✅ Migración `0011_rename_index_for_consistency` aplicada exitosamente
- ✅ Índice `idx_orders_status_created` creado en base de datos

### Índices Existentes

- ✅ `idx_orders_user` - Índice simple en `user`
- ✅ `idx_orders_status` - Índice simple en `status`
- ✅ `idx_orders_created` - Índice simple en `created_at`
- ✅ `idx_orders_user_created` - Índice compuesto en `['user', 'created_at']`
- ✅ `idx_orders_status_created` - Índice compuesto en `['status', 'created_at']` (NUEVO)

### Queries que Usan los Índices

**Query actual en `views.py`:**
```python
Order.objects.filter(user=request.user).order_by('-created_at')
```
- ✅ Usa `idx_orders_user_created` (perfecto)

**Admin de Django:**
```python
list_filter = ('status', 'created_at')
```
- ✅ Puede usar `idx_orders_status_created` cuando se filtra por status y ordena por fecha

### Correcciones Aplicadas

#### Migración 0011: Renombrar Índice para Consistencia
- ✅ Creada migración `0011_rename_index_for_consistency.py`
- ✅ Renombrado `idx_order_status_created` → `idx_orders_status_created`
- ✅ Modelo actualizado con el nombre correcto
- ✅ Migración aplicada exitosamente
- ✅ Todos los tests pasan (38/38)

### Estado Final

- ✅ Índice creado correctamente
- ✅ Nombres consistentes (idx_orders_*)
- ✅ Modelo y BD sincronizados
- ✅ Tests pasando
- ✅ Sin problemas actuales o futuros identificados

---

## 4. Acción 9: Constraints y Validaciones

**Fecha:** 2025-11-15  
**Estado:** ✅ COMPLETADO Y VERIFICADO

### Migraciones Aplicadas

- ✅ `products.0012_add_constraints` - Aplicada
- ✅ `orders.0012_add_constraints` - Aplicada

### Constraints Implementados

#### Product Model (6 total)
- ✅ `pct_range_0_100` - Descuento entre 0-100%
- ✅ `only_one_discount_mode` - Solo un tipo de descuento
- ✅ `product_stock_qty_non_negative` - Stock >= 0
- ✅ `product_stock_reserved_non_negative` - Reservado >= 0
- ✅ `product_stock_reserved_lte_qty` - Reservado <= Stock
- ✅ `product_price_positive` - **NUEVO**: Precio > 0

#### Order Model (2 total)
- ✅ `order_total_amount_positive` - **NUEVO**: total_amount > 0
- ✅ `order_shipping_cost_non_negative` - **NUEVO**: shipping_cost >= 0

#### OrderItem Model (3 total)
- ✅ `order_item_quantity_positive` - **NUEVO**: quantity > 0
- ✅ `order_item_unit_price_positive` - **NUEVO**: unit_price > 0
- ✅ `order_item_total_price_positive` - **NUEVO**: total_price > 0

### Resumen de Constraints Totales

| Modelo | Constraints Totales | Nuevos en Acción 9 |
|--------|-------------------|-------------------|
| Product | 6 | 1 |
| Order | 2 | 2 |
| OrderItem | 3 | 3 |
| **TOTAL** | **11** | **6** |

### Compatibilidad Django 6.0

- ✅ Todos los constraints usan `condition` en lugar de `check` (deprecado)
- ✅ Sin warnings de `RemovedInDjango60Warning`
- ✅ Código preparado para futuras versiones

### Estado Final

- ✅ No hay problemas detectados
- ✅ No hay errores
- ✅ No hay warnings
- ✅ Todo está en orden
- ✅ Listo para producción

---

## 5. Acción 10: Tabla de Configuración (StoreConfig)

**Fecha:** 2025-11-15  
**Estado:** ✅ COMPLETADO Y VERIFICADO

### Archivos Creados

1. ✅ `apps/common/models.py` - Modelo `StoreConfig`
2. ✅ `apps/common/migrations/0001_create_store_config.py` - Migración con datos iniciales
3. ✅ `apps/common/admin.py` - Interface de administración

### Características Implementadas

#### Modelo StoreConfig
- ✅ Campo `key` (CharField, primary_key, unique)
- ✅ Campo `value` (TextField)
- ✅ Campo `data_type` (CharField con choices)
- ✅ Campo `description` (TextField, opcional)
- ✅ Campo `is_public` (BooleanField)
- ✅ Campo `updated_at` (DateTimeField, auto_now)
- ✅ Campo `updated_by` (ForeignKey a User, nullable)
- ✅ Método `get_value()` - Convierte value según data_type
- ✅ Método `get()` - Obtiene configuración con cache
- ✅ Método `save()` - Invalida cache al guardar

#### Tipos de Dato Soportados
- ✅ `string` - Texto
- ✅ `int` - Número Entero
- ✅ `decimal` - Número Decimal
- ✅ `boolean` - Booleano
- ✅ `json` - JSON

#### Datos Iniciales Creados
- ✅ `tax_rate` = 19 (int) - Tasa de IVA en Chile (%)
- ✅ `free_shipping_threshold` = 50000 (int) - Monto mínimo para envío gratis (CLP)
- ✅ `currency` = CLP (string) - Moneda del sistema
- ✅ `maintenance_mode` = false (boolean) - Modo mantención
- ✅ `stock_reservation_timeout` = 30 (int) - Minutos antes de liberar reserva
- ✅ `max_items_per_order` = 50 (int) - Cantidad máxima de items por orden

### Uso del Modelo

```python
from apps.common.models import StoreConfig

# Con cache automático
tax_rate = StoreConfig.get('tax_rate', default=19)
free_shipping = StoreConfig.get('free_shipping_threshold', default=50000)
currency = StoreConfig.get('currency', default='CLP')
maintenance = StoreConfig.get('maintenance_mode', default=False)
```

### Estado Final

- ✅ Todos los requisitos del plan original cumplidos
- ✅ Funcionalidad adicional (cache) implementada
- ✅ Admin interface completa
- ✅ Datos iniciales creados
- ✅ Listo para uso en producción

---

## 6. Verificación del Plan Original de Refactorización

**Fecha:** 2025-11-15  
**Objetivo:** Verificar que las 9 acciones implementadas coincidan con el plan original

### Resumen de Acciones Implementadas

| Acción | Estado | Migraciones | Modelos Afectados |
|--------|--------|-------------|-------------------|
| 1. Shipping Snapshots | ✅ | orders.0005 | Order, OrderItem |
| 2. Payment Transactions | ✅ | orders.0008 | PaymentTransaction |
| 3. (No identificada) | ⚠️ | - | - |
| 4. ProductPriceHistory | ✅ | products.0007, 0008 | ProductPriceHistory |
| 5. Category Hierarchy | ✅ | products.0009 | Category |
| 6. Inventory Control | ✅ | products.0010 | Product, InventoryMovement |
| 7. Shipping Rules + Weight | ✅ | orders.0009, products.0011 | ShippingCarrier, ShippingRule, Product |
| 8. Performance Indexes | ✅ | orders.0010, 0011 | Order |
| 9. Constraints | ✅ | products.0012, orders.0012 | Product, Order, OrderItem |
| 10. Config Table | ✅ | common.0001 | StoreConfig |

### Verificaciones de Calidad

#### Migraciones
- ✅ Todas las migraciones aplicadas correctamente
- ✅ Sin errores en `python manage.py check`
- ✅ Sin errores en `python manage.py migrate --plan`
- ✅ Nomenclatura consistente

#### Modelos
- ✅ Constraints definidos correctamente
- ✅ Índices optimizados
- ✅ Relaciones ForeignKey con `related_name` explícito
- ✅ Campos de auditoría (`created_at`, `updated_at`)

#### Tests
- ✅ 38 tests pasando
- ✅ Sin warnings de deprecación
- ✅ Tests para funcionalidades críticas

#### Compatibilidad
- ✅ Django 6.0 compatible (sin warnings)
- ✅ PostgreSQL compatible
- ✅ Sin breaking changes en API

---

## 7. Scripts de Debugging

**Ubicación:** `backend/docs/scripts/debugging/`

### Scripts Disponibles

#### `analyze_payment_transactions.py`
Análisis exhaustivo de la tabla `payment_transactions`:
- Columnas en BD vs Modelo Django
- Índices y Foreign Keys
- Comparación modelo vs BD
- Estado de campos críticos

**Uso:**
```bash
# Desde condorshop/backend
python manage.py shell < docs/scripts/debugging/analyze_payment_transactions.py
```

#### `inspect_payment_table.py`
Inspección rápida de la estructura de `payment_transactions`:
- Columnas actuales
- Índices
- Foreign Keys
- Muestra de datos

**Uso:**
```bash
# Desde condorshop/backend
python docs/scripts/debugging/inspect_payment_table.py
```

### Notas

- Estos scripts son herramientas de desarrollo/debugging
- No afectan el funcionamiento del proyecto
- Pueden ejecutarse en cualquier momento para análisis
- Útiles para debugging de migraciones y estructura de BD
- Compatibles con PostgreSQL y MySQL (detección automática)

---

## 8. Informe de Auditoría - Migración a CLP Enteros y Optimización de Índices

**Fecha:** Noviembre 2025  
**Estado:** ✅ COMPLETADO

### Resumen Ejecutivo

- Conversión completa de montos a **enteros CLP** en modelos, vistas, serializers y tests.
- Refuerzo de integridad de carritos (`total_price`, índices y `UniqueConstraint`).
- Optimización de índices:
  - `products`: nuevo índice compuesto `idx_product_active_created`.
  - `cart_items`: sincronización de `total_price` + índices `idx_cartitem_cart_product`, `idx_cartitem_product` y `uq_cartitem_cart_product`.
  - `orders`: uso validado de `idx_order_customer_email`.
- Nuevo comando `python manage.py analyze_indexes` para inspeccionar planes de ejecución.

### Cambios Aplicados

- **Migraciones:**
  - `cart.0004_sync_total_price_column` y `cart.0005_ensure_cart_indexes`
  - `products.0005_product_idx_product_active_created`
- **Management command:** `apps.common.management.commands.analyze_indexes`
- **Ajustes en lógica:** checkout/cart para trabajar con enteros

### Análisis de Índices (12-nov-2025)

| Consulta | Índice utilizado | Observaciones |
| --- | --- | --- |
| Listado productos activos (`ordering=-created_at`) | `idx_product_active_created` | Evita `filesort`; costo estimado 1 fila |
| Búsqueda `name__istartswith=a` | `idx_product_name` | *Range scan* sobre prefijo `LIKE 'a%'` |
| Ítems de carrito (cart/product) | `uq_cartitem_cart_product` / `idx_cartitem_cart_product` | Lookup inmediato (`Rows fetched before execution`) |
| Órdenes por correo (`customer_email`) | `idx_order_customer_email` | Lookup directo, costo 0.35 |

> El comando todavía no soporta `--format=json`; se documentó el resultado en texto plano.

### Resultados Detallados de EXPLAIN

**Listado productos activos por fecha de creación:**
```
SELECT ... FROM `products` WHERE `products`.`active` = True ORDER BY `products`.`created_at` DESC
-> Index lookup on products using idx_product_active_created (active=1)  (cost=1 rows=5)
```

**Búsqueda por prefijo (name__istartswith='a'):**
```
SELECT ... FROM `products` WHERE `products`.`name` LIKE 'a%'
-> Index range scan on products using idx_product_name ... (cost=0.71 rows=1)
```

**Ítems de carrito por cart/product:**
```
SELECT ... FROM `cart_items` WHERE (`cart_items`.`cart_id` = 9 AND `cart_items`.`product_id` IN (5))
-> Rows fetched before execution  (cost=0..0 rows=1)
```

**Órdenes por correo:**
```
SELECT ... FROM `orders` WHERE `orders`.`customer_email` = 'demo@example.com'
-> Index lookup on orders using idx_order_customer_email (customer_email='demo@example.com')  (cost=0.35 rows=1)
```

### Riesgos y Limitaciones

- `icontains` sigue sin usar índice en MySQL; se recomienda exponer `name__istartswith` para búsquedas rápidas y evaluar `FULLTEXT` a futuro si se requiere texto libre.
- Los índices recién sincronizados (`cart_items`) dependen de migraciones incrementales; se documentó el motivo en `0004`/`0005`.
- `audit.AuditLog` continúa sin política de retención (crece indefinidamente).

### Validaciones Ejecutadas

- ✅ `python manage.py analyze_indexes`
- ✅ `python manage.py migrate`
- ✅ `python manage.py check`
- ✅ `pytest -q` (21 pruebas pasando, incluye smoke tests en `tests/smoke/`)
- ✅ Pruebas manuales API: listado ordenado, prefijos, carrito invitado, `shipping-quote`, creación de orden (todos los montos en enteros CLP)

### Próximos Pasos Sugeridos

- Monitorear `analyze_indexes` en staging tras carga real.
- Evaluar `FULLTEXT` o buscador externo si las búsquedas libres se vuelven críticas.
- Planificar política de retención para `audit_log` y procesos de archivado.

---

## 9. Plan de Correcciones y Seguimiento

**Fecha:** Noviembre 2025  
**Estado:** ✅ COMPLETADO

### Estado Actual

- ✅ Migraciones aplicadas: `cart.0004`, `cart.0005`, `products.0005`.
- ✅ Índices críticos operativos (confirmados con `analyze_indexes`).
- ✅ Documentación actualizada.

### Tareas Completadas

- ✅ `python manage.py analyze_indexes` registrado
- ✅ Verificación manual de API (listado, prefijo, carrito invitado, shipping quote, creación de orden) con montos enteros
- ✅ Smoke tests y `pytest -q` en verde (21 tests)

### Pendientes y Observaciones

1. **Búsqueda de texto libre:** evaluar `FULLTEXT` o motor externo si la demanda crece (actualmente se recomienda `name__istartswith`).
2. **Retención de auditoría:** definir proceso de limpieza/archivado para `audit.AuditLog`.
3. **Revisión periódica de índices:** ejecutar `python manage.py analyze_indexes` tras cargas significativas o cambios de datos.

### Verificación en Producción

- Ejecutar `python manage.py analyze_indexes` y capturar los planes en un dashboard/issue.
- Monitorear métricas de MySQL (`Handler_read_next`, `Handler_read_key`) para confirmar uso de índices.
- Revisar logs de error (`backend/logs/django.log`) en los primeros despliegues posteriores al cambio.

### Rollback

Si es necesario revertir:

1. Restaurar backup de base de datos anterior a `cart.0004`/`0005` y `products.0005`.
2. Ejecutar `python manage.py migrate cart 0003` y `python manage.py migrate products 0004`.
3. Revertir el código al commit previo (sin campos enteros) y volver a desplegar.

### Comandos Útiles

- `python manage.py analyze_indexes`
- `python manage.py check`
- `pytest -q`
- `python manage.py showmigrations`
- `python manage.py dumpdata products.Product --indent 2`
- `python manage.py dbshell` (para inspecciones puntuales)

---

## 📝 Notas Finales

Este documento consolida toda la documentación histórica del desarrollo del proyecto CondorShop, incluyendo:

- Correcciones de bugs críticos
- Migraciones complejas
- Implementación de funcionalidades
- Verificaciones de calidad
- Scripts de debugging
- Informes de auditoría
- Planes de correcciones y seguimiento

**Última actualización:** Noviembre 2025  
**Mantenido por:** Equipo de desarrollo CondorShop

