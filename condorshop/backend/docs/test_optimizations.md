# Guía de Pruebas para Optimizaciones

Esta guía describe cómo verificar que todas las optimizaciones implementadas funcionan correctamente.

## 📋 Checklist de Verificación

### 1. Verificar Índices en Base de Datos

```bash
# Ejecutar comando de verificación (recomendado)
python manage.py verify_indexes
```

Este comando verificará que todos los índices opcionales se crearon correctamente:
- ✅ `idx_product_description_trgm` (GIN para products.description)
- ✅ `idx_cart_active_session` (parcial para carts.session_token)
- ✅ `idx_hero_slide_active_order_created` (compuesto para hero_carousel_slides)
- ✅ `idx_payment_tx_order_status` (compuesto para payment_transactions)

O verificar manualmente en PostgreSQL:
```sql
-- Verificar índice GIN de description
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'products' 
AND indexname = 'idx_product_description_trgm';

-- Verificar índice parcial de session_token
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'carts' 
AND indexname = 'idx_cart_active_session';

-- Verificar índice compuesto de hero_carousel_slides
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'hero_carousel_slides' 
AND indexname = 'idx_hero_slide_active_order_created';

-- Verificar índice compuesto de payment_transactions
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'payment_transactions' 
AND indexname = 'idx_payment_tx_order_status';
```

---

## 🧪 Pruebas Manuales

### 2. Verificar Concurrencia en Carrito (FASE 1)

**Objetivo:** Confirmar que no hay sobreventa de stock con `select_for_update()`.

**Pasos:**

1. **Preparar ambiente:**
   - Crear un producto con stock limitado (ej: stock_qty = 5)
   - Tener dos sesiones/ventanas del navegador abiertas

2. **Prueba de concurrencia:**
   - En la sesión 1: Intentar agregar 4 unidades al carrito
   - En la sesión 2 (al mismo tiempo): Intentar agregar 3 unidades al carrito
   - **Resultado esperado:** Solo una de las dos operaciones debería tener éxito completamente
   - Verificar que el stock final es correcto (no puede ser negativo)

3. **Verificar con logs:**
   ```bash
   # En settings.py, habilitar logging SQL:
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'django.db.backends': {
               'level': 'DEBUG',
               'handlers': ['console'],
           },
       },
   }
   ```
   - Verificar que se ejecuta `SELECT ... FOR UPDATE` en las queries

**Comandos para probar:**
```bash
# Terminal 1
curl -X POST http://localhost:8000/api/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: session1" \
  -d '{"product_id": 1, "quantity": 4}'

# Terminal 2 (ejecutar casi simultáneamente)
curl -X POST http://localhost:8000/api/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: session2" \
  -d '{"product_id": 1, "quantity": 3}'
```

---

### 3. Verificar Optimización de shipping_quote (FASE 2)

**Objetivo:** Confirmar que `shipping_quote` no hace N+1 queries.

**Pasos:**

1. **Habilitar django-debug-toolbar** (si está instalado) o logging SQL:
   ```python
   # settings.py
   if DEBUG:
       LOGGING = {
           'version': 1,
           'disable_existing_loggers': False,
           'handlers': {
               'console': {
                   'class': 'logging.StreamHandler',
               },
           },
           'loggers': {
               'django.db.backends': {
                   'level': 'DEBUG',
                   'handlers': ['console'],
               },
           },
       }
   ```

2. **Hacer request con varios productos:**
   ```bash
   curl -X POST http://localhost:8000/api/checkout/shipping-quote \
     -H "Content-Type: application/json" \
     -d '{
       "region": "Región Metropolitana",
       "cart_items": [
         {"product_id": 1, "quantity": 2},
         {"product_id": 2, "quantity": 1},
         {"product_id": 3, "quantity": 3},
         {"product_id": 4, "quantity": 1},
         {"product_id": 5, "quantity": 2}
       ]
     }'
   ```

3. **Verificar logs:**
   - **Antes:** Debería haber 5 queries SELECT (una por producto)
   - **Después:** Debería haber solo 1 query SELECT con `filter(id__in=[1,2,3,4,5])`

**Resultado esperado:** 1 query para productos + queries adicionales para categorías (si hay select_related)

---

### 4. Verificar Optimización de create_order (FASE 3)

**Objetivo:** Confirmar que `create_order` usa `bulk_create` y `bulk_update`.

**Pasos:**

1. **Crear una orden con varios productos:**
   ```bash
   curl -X POST http://localhost:8000/api/orders/create \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{
       "shipping_region": "Región Metropolitana",
       "shipping_street": "Calle Test 123",
       "shipping_city": "Santiago",
       "shipping_postal_code": "12345",
       "customer_name": "Test User",
       "customer_email": "test@example.com"
     }'
   ```

2. **Verificar con logs SQL:**
   - **Snapshots:** Debería haber 1 `INSERT` múltiple (bulk_create) en lugar de N INSERTs
   - **InventoryMovements:** Debería haber 1 `SELECT` con `filter(id__in=[...])` y 1 `UPDATE` múltiple (bulk_update)

3. **Verificar en base de datos:**
   ```sql
   -- Verificar que se crearon los snapshots
   SELECT COUNT(*) FROM order_item_snapshots;
   
   -- Verificar que los movimientos se actualizaron
   SELECT COUNT(*) FROM inventory_movements 
   WHERE reference_type = 'order' AND reference_id IS NOT NULL;
   ```

**Resultado esperado:** 
- Todos los snapshots creados correctamente
- Todos los movimientos de inventario vinculados al order_id
- Número reducido de queries SQL

---

### 5. Verificar Optimización de view_cart (FASE 3)

**Objetivo:** Confirmar que `view_cart` usa `bulk_update`.

**Pasos:**

1. **Crear carrito con varios productos que tengan precios diferentes:**
   - Agregar productos al carrito
   - Cambiar precios de algunos productos (aplicar descuentos)

2. **Ver el carrito:**
   ```bash
   curl -X GET http://localhost:8000/api/cart/ \
     -H "Authorization: Bearer <token>"
   ```

3. **Verificar con logs SQL:**
   - **Antes:** N queries UPDATE (una por item que cambió)
   - **Después:** 1 query UPDATE múltiple (bulk_update)

**Resultado esperado:** 1 UPDATE con múltiples filas en lugar de N UPDATEs individuales

---

### 6. Verificar Corrección en Admin (FASE 4)

**Objetivo:** Confirmar que el panel de admin funciona sin errores.

**Pasos:**

1. **Acceder al admin:**
   - Ir a `http://localhost:8000/admin/`
   - Navegar a `Orders > Payments`

2. **Verificar columna "Transacción actual":**
   - Debería mostrar el `webpay_buy_order` o 'N/A'
   - **NO** debería mostrar errores en la consola del servidor
   - **NO** debería mostrar "AttributeError" o referencias a `buy_order`

3. **Verificar transacciones:**
   - Ir a `Orders > Payment Transactions`
   - Verificar que se pueden ver sin errores

**Resultado esperado:** Sin errores en la consola, columna muestra datos correctos

---

## 📊 Métricas de Rendimiento

### Consultas por Endpoint (antes vs después)

| Endpoint | Query Type | Antes | Después | Mejora |
|----------|------------|-------|---------|--------|
| `shipping_quote` (5 productos) | SELECT productos | 5 | 1 | 80% ↓ |
| `create_order` (5 productos) | INSERT snapshots | 5 | 1 | 80% ↓ |
| `create_order` (5 productos) | UPDATE movimientos | 5 | 1 | 80% ↓ |
| `view_cart` (5 items con precio actualizado) | UPDATE items | 5 | 1 | 80% ↓ |

---

## 🔍 Debugging con django-debug-toolbar

Si tienes `django-debug-toolbar` instalado:

1. **Habilitar en settings.py:**
   ```python
   if DEBUG:
       INSTALLED_APPS += ['debug_toolbar']
       MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
       INTERNAL_IPS = ['127.0.0.1']
   ```

2. **Navegar a cualquier endpoint** y ver:
   - Número de queries SQL
   - Tiempo de ejecución
   - Detalles de cada query

---

## ⚠️ Problemas Comunes

### Error: "Index already exists"
- **Causa:** El índice ya fue creado por `optimize_db_indexes.py`
- **Solución:** No es un problema, el índice existe y funciona

### Error: "relation does not exist"
- **Causa:** Las migraciones no se aplicaron
- **Solución:** Ejecutar `python manage.py migrate`

### No se ven mejoras en rendimiento
- **Causa:** Volumen de datos bajo o caché activo
- **Solución:** Probar con mayor volumen de datos o desactivar caché temporalmente

---

## ✅ Criterios de Éxito

- [ ] Todas las migraciones aplicadas sin errores
- [ ] Índices verificados en base de datos
- [ ] Prueba de concurrencia: no hay sobreventa de stock
- [ ] `shipping_quote`: solo 1 query SELECT para productos
- [ ] `create_order`: snapshots creados con bulk_create
- [ ] `create_order`: movimientos actualizados con bulk_update
- [ ] `view_cart`: precios actualizados con bulk_update
- [ ] Admin de Payment: muestra `webpay_buy_order` sin errores

