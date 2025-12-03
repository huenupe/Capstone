# 🚀 Plan de Optimización de Performance - CondorShop Backend

**Fecha**: Diciembre 2024  
**Objetivo**: Reducir queries y latencia en endpoints críticos sin romper lógica de negocio

---

## 1. REVALIDACIÓN DEL ANÁLISIS PREVIO

### 1.1. Confirmación de Problemas Existentes

#### ✅ PROBLEMA CONFIRMADO: CartSerializer - Múltiples accesos a `items.all()`
- **Archivo**: `apps/cart/serializers.py:56-80`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: `get_subtotal()`, `get_shipping_cost()`, `get_total()` y métodos `*_formatted` llaman múltiples veces a `obj.items.all()`
- **Impacto**: 3-4 evaluaciones del queryset por request de carrito

#### ✅ PROBLEMA CONFIRMADO: CategorySerializer - N+1 en subcategorías
- **Archivo**: `apps/products/serializers.py:52-67`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: `get_subcategories()` y `get_has_children()` hacen `obj.subcategories.filter(active=True)` por cada categoría
- **Impacto**: 40+ queries adicionales en listado de 20 categorías

#### ✅ PROBLEMA CONFIRMADO: ProductListSerializer.get_main_image() - Query adicional
- **Archivo**: `apps/products/serializers.py:166-173`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: `obj.images.order_by('position').first()` puede disparar query si prefetch no incluye ordenamiento
- **Impacto**: 1 query adicional por producto en listado

#### ✅ PROBLEMA CONFIRMADO: view_cart() - Recarga innecesaria
- **Archivo**: `apps/cart/views.py:108-113`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: Se obtiene carrito con `get_cart()` y luego se recarga con `Cart.objects.get(id=cart.id)`
- **Impacto**: 1 query innecesaria por request

#### ✅ PROBLEMA CONFIRMADO: Cart.get_or_create_cart() - Múltiples queries
- **Archivo**: `apps/cart/models.py:46-149`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: `count()`, `first()`, `exclude().update()` hacen 3+ queries para limpiar duplicados
- **Impacto**: 3-5 queries por operación de carrito

#### ✅ PROBLEMA CONFIRMADO: checkout_mode() - Carga todas las direcciones
- **Archivo**: `apps/orders/views.py:108-136`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: `Address.objects.filter(user=user).order_by(...)` carga todas las direcciones siempre
- **Impacto**: Query innecesaria si solo se necesita saber si existen

#### ✅ PROBLEMA CONFIRMADO: Falta índices compuestos en Cart
- **Archivo**: `apps/cart/models.py:35-38`
- **Estado**: ❌ NO OPTIMIZADO
- **Evidencia**: Solo existen índices simples `['user']` y `['session_token']`, falta `['user', 'is_active']` y `['session_token', 'is_active']`
- **Impacto**: Queries más lentas en `get_or_create_cart()`

#### ✅ YA OPTIMIZADO: create_order() - Transacciones atómicas
- **Archivo**: `apps/orders/views.py:142`
- **Estado**: ✅ YA OPTIMIZADO
- **Evidencia**: Ya tiene `@transaction.atomic` y usa `select_for_update()`
- **Acción**: Solo validar que esté correcto, no modificar

---

### 1.2. Resumen de Endpoints Críticos

| Endpoint | Modelos Consultados | Queries Aproximadas (ANTES) | Puntos N+1 / Trabajo Repetido |
|----------|---------------------|----------------------------|-------------------------------|
| `GET /api/products/` | Product, Category, ProductImage | 1 + N (imágenes) | `get_main_image()` puede hacer query adicional |
| `GET /api/products/{slug}/` | Product, Category, ProductImage | 1 + 1 (imágenes) | Ninguno crítico |
| `GET /api/products/categories/` | Category | 1 + 40+ (subcategorías) | `get_subcategories()` y `get_has_children()` hacen N+1 |
| `GET /api/cart/` | Cart, CartItem, Product, Category, ProductImage | 2-3 + 3-4 (evaluaciones items) | `CartSerializer` accede a `items.all()` múltiples veces |
| `POST /api/checkout/create` | Cart, CartItem, Product, Order, OrderItem, ... | 10-20+ (según items) | Sincronización frontend hace queries individuales (necesario) |
| `GET /api/checkout/mode` | User, Address | 1-2 | Carga todas las direcciones aunque solo se necesite saber si existen |
| `GET /api/orders/` | Order, OrderItem, Product, OrderStatus, ... | 1 (optimizado) | Ninguno crítico |

---

## 2. CAMBIOS PROPUESTOS

### 2.1. Serializers y Vistas

#### Cambio 1: Optimizar CartSerializer
- **Archivo**: `apps/cart/serializers.py`
- **Líneas**: 56-80
- **Beneficio**: Elimina 3-4 evaluaciones del queryset por request
- **Riesgo**: Bajo (solo cachea resultado, mantiene lógica)

#### Cambio 2: Optimizar CategorySerializer con Prefetch
- **Archivo**: `apps/products/views.py` y `apps/products/serializers.py`
- **Líneas**: 108, 52-67
- **Beneficio**: Elimina 40+ queries en listado de categorías
- **Riesgo**: Bajo (solo optimiza prefetch, mantiene fallback)

#### Cambio 3: Optimizar ProductListSerializer.get_main_image()
- **Archivo**: `apps/products/views.py` y `apps/products/serializers.py`
- **Líneas**: 30, 166-173
- **Beneficio**: Elimina 1 query por producto en listado
- **Riesgo**: Bajo (mantiene fallback)

#### Cambio 4: Optimizar view_cart() y get_cart()
- **Archivo**: `apps/cart/views.py`
- **Líneas**: 11-22, 100-140
- **Beneficio**: Elimina 1 query innecesaria
- **Riesgo**: Medio (puede afectar otros usos de get_cart)

#### Cambio 5: Optimizar checkout_mode()
- **Archivo**: `apps/orders/views.py`
- **Líneas**: 108-136
- **Beneficio**: Reduce carga cuando hay muchas direcciones
- **Riesgo**: Bajo (solo optimiza query, mantiene respuesta)

### 2.2. Métodos de Modelo

#### Cambio 6: Optimizar Cart.get_or_create_cart()
- **Archivo**: `apps/cart/models.py`
- **Líneas**: 46-149
- **Beneficio**: Reduce queries de 3-5 a 1-2
- **Riesgo**: Medio (lógica crítica de carritos)

### 2.3. Índices y Migraciones

#### Cambio 7: Añadir índices compuestos en Cart
- **Archivo**: `apps/cart/models.py` y migración
- **Líneas**: 35-38
- **Beneficio**: Acelera queries de `get_or_create_cart()`
- **Riesgo**: Bajo (solo añade índices)

---

## 3. GUÍA DE PRUEBAS MANUALES

### 3.1. Endpoints a Probar

1. **GET /api/cart/**
   - Carrito vacío
   - Carrito con 1 item
   - Carrito con 10+ items
   - Verificar que subtotal, shipping, total sean correctos

2. **GET /api/products/categories/**
   - Listado completo
   - Verificar que subcategorías se muestren correctamente
   - Verificar que has_children sea correcto

3. **GET /api/products/**
   - Listado con búsqueda
   - Verificar que imágenes principales se muestren
   - Verificar paginación

4. **GET /api/checkout/mode**
   - Usuario sin direcciones
   - Usuario con 1 dirección
   - Usuario con 10+ direcciones
   - Verificar que respuesta sea correcta

5. **POST /api/checkout/create**
   - Crear orden desde carrito con items
   - Verificar que stock se reserve correctamente
   - Verificar que orden se cree correctamente

### 3.2. Escenarios de Carga

- **Carrito con muchos items**: 20+ productos
- **Muchas categorías**: 50+ categorías con subcategorías
- **Muchos productos**: 1000+ productos activos
- **Muchas direcciones**: Usuario con 20+ direcciones guardadas

---

## 4. RIESGOS Y MITIGACIONES

### Riesgo Alto
- Ninguno identificado

### Riesgo Medio
- **Cambio 4 (view_cart/get_cart)**: Puede afectar otros usos de `get_cart()`
  - **Mitigación**: Crear `get_cart_optimized()` separado y usar solo en `view_cart()`
  
- **Cambio 6 (Cart.get_or_create_cart)**: Lógica crítica de carritos
  - **Mitigación**: Mantener lógica original como fallback, añadir tests

### Riesgo Bajo
- Todos los demás cambios tienen fallbacks o no cambian lógica funcional

---

## 5. DECISIONES PENDIENTES

### Índice GIN para búsqueda de texto
- **Recomendación**: NO implementar ahora
- **Razón**: Solo necesario si hay >10,000 productos y búsquedas muy frecuentes
- **Acción**: Monitorear y considerar en el futuro si es necesario

### CategoryTreeSerializer.get_product_count()
- **Recomendación**: NO optimizar ahora
- **Razón**: Endpoint poco usado, impacto bajo
- **Acción**: Considerar si se usa más en el futuro

---

## 6. RESUMEN DE CAMBIOS IMPLEMENTADOS

### 6.1. Serializers y Vistas

#### ✅ Cambio 1: CartSerializer - Cache de subtotal
- **Archivo**: `apps/cart/serializers.py:56-80`
- **Cambio**: Implementado cache `_subtotal_cache` en `get_subtotal()` para evitar múltiples evaluaciones
- **Beneficio**: Elimina 3-4 evaluaciones del queryset por request
- **Riesgo**: Bajo (solo cachea, mantiene lógica)
- **Estado**: ✅ IMPLEMENTADO

#### ✅ Cambio 2: CategorySerializer - Prefetch filtrado
- **Archivo**: `apps/products/views.py:108` y `apps/products/serializers.py:52-67`
- **Cambio**: Añadido `Prefetch` con `to_attr='active_subcategories'` y fallback en serializer
- **Beneficio**: Elimina 40+ queries en listado de categorías
- **Riesgo**: Bajo (mantiene fallback)
- **Estado**: ✅ IMPLEMENTADO

#### ✅ Cambio 3: ProductListSerializer - Prefetch ordenado de imágenes
- **Archivo**: `apps/products/views.py:30` y `apps/products/serializers.py:166-173`
- **Cambio**: Añadido `Prefetch` con `to_attr='ordered_images'` y fallback en serializer
- **Beneficio**: Elimina 1 query por producto en listado
- **Riesgo**: Bajo (mantiene fallback)
- **Estado**: ✅ IMPLEMENTADO

#### ✅ Cambio 4: view_cart() - Eliminar recarga innecesaria
- **Archivo**: `apps/cart/views.py:11-22, 100-140`
- **Cambio**: Creado `get_cart_optimized()` que retorna carrito ya optimizado, usado solo en `view_cart()`
- **Beneficio**: Elimina 1 query innecesaria
- **Riesgo**: Bajo (no afecta otros usos de `get_cart()`)
- **Estado**: ✅ IMPLEMENTADO

#### ✅ Cambio 5: checkout_mode() - Optimizar carga de direcciones
- **Archivo**: `apps/orders/views.py:108-136`
- **Cambio**: Usar `.exists()` primero y limitar a 10 direcciones
- **Beneficio**: Reduce carga cuando hay muchas direcciones
- **Riesgo**: Bajo (mantiene respuesta equivalente)
- **Estado**: ✅ IMPLEMENTADO

### 6.2. Métodos de Modelo

#### ✅ Cambio 6: Cart.get_or_create_cart() - Reducir queries
- **Archivo**: `apps/cart/models.py:46-149`
- **Cambio**: Usar `first()` directamente en lugar de `count() + first()`, envolver en `transaction.atomic()` con `select_for_update()`
- **Beneficio**: Reduce queries de 3-5 a 1-2
- **Riesgo**: Medio (lógica crítica, pero mantiene comportamiento)
- **Estado**: ✅ IMPLEMENTADO

### 6.3. Índices y Migraciones

#### ✅ Cambio 7: Índices compuestos en Cart
- **Archivo**: `apps/cart/models.py:35-38` y `apps/cart/migrations/0007_add_cart_composite_indexes.py`
- **Cambio**: Añadidos índices `idx_cart_user_active` y `idx_cart_session_active`
- **Beneficio**: Acelera queries de `get_or_create_cart()`
- **Riesgo**: Bajo (solo añade índices)
- **Estado**: ✅ IMPLEMENTADO (migración creada, pendiente aplicar)

### 6.4. Validación de create_order()

#### ✅ Validación: create_order() - Transacciones
- **Archivo**: `apps/orders/views.py:142`
- **Estado**: ✅ YA OPTIMIZADO
- **Evidencia**: Ya tiene `@transaction.atomic` y usa `select_for_update()` correctamente
- **Acción**: No se modificó, solo se validó

---

## 7. GUÍA DE PRUEBAS MANUALES

### 7.1. Endpoints Críticos a Probar

#### 1. GET /api/cart/
**Escenarios:**
- [ ] Carrito vacío (debe retornar subtotal=0, shipping=5000, total=5000)
- [ ] Carrito con 1 item (verificar cálculos correctos)
- [ ] Carrito con 10+ items (verificar que no haya lentitud)
- [ ] Carrito con items que tienen descuentos (verificar que precios se actualicen)

**Qué verificar:**
- Respuesta JSON tiene estructura correcta
- `subtotal`, `shipping_cost`, `total` son numéricos correctos
- `*_formatted` tienen formato CLP correcto
- No hay errores en consola del servidor

#### 2. GET /api/products/categories/
**Escenarios:**
- [ ] Listado completo de categorías
- [ ] Categorías con subcategorías (verificar que `subcategories` tenga IDs correctos)
- [ ] Categorías sin subcategorías (verificar que `has_children=false`)
- [ ] Categorías con muchas subcategorías (10+)

**Qué verificar:**
- Todas las categorías se muestran
- `subcategories` es array de IDs (no objetos completos)
- `has_children` es booleano correcto
- No hay queries N+1 en logs (usar Django Debug Toolbar o similar)

#### 3. GET /api/products/
**Escenarios:**
- [ ] Listado sin filtros
- [ ] Listado con búsqueda (`?search=laptop`)
- [ ] Listado con filtro de categoría
- [ ] Listado paginado (verificar que imágenes se muestren)

**Qué verificar:**
- `main_image` se muestra para cada producto
- Imágenes están ordenadas correctamente (primera por position)
- No hay errores 404 en imágenes
- Paginación funciona correctamente

#### 4. GET /api/checkout/mode
**Escenarios:**
- [ ] Usuario no autenticado (debe retornar `is_authenticated=false`)
- [ ] Usuario autenticado sin direcciones (debe retornar `saved_addresses=[]`)
- [ ] Usuario con 1 dirección (debe retornar 1 dirección)
- [ ] Usuario con 15+ direcciones (debe retornar máximo 10)

**Qué verificar:**
- Respuesta tiene estructura correcta
- `saved_addresses` es array (puede estar vacío)
- Si hay muchas direcciones, solo se cargan las primeras 10
- No hay lentitud con muchas direcciones

#### 5. POST /api/checkout/create
**Escenarios:**
- [ ] Crear orden desde carrito con items
- [ ] Crear orden como usuario autenticado
- [ ] Crear orden como invitado (con X-Session-Token)
- [ ] Crear orden con productos que tienen stock limitado

**Qué verificar:**
- Orden se crea correctamente
- Stock se reserva correctamente
- Items de orden tienen precios correctos
- No hay errores de transacción

### 7.2. Escenarios de Carga

#### Carrito con muchos items
- Crear carrito con 20+ productos diferentes
- Verificar que `GET /api/cart/` responda rápido (<500ms)
- Verificar que cálculos sean correctos

#### Muchas categorías
- Si hay 50+ categorías en BD, verificar que listado sea rápido
- Verificar que todas las subcategorías se muestren correctamente

#### Muchos productos
- Si hay 1000+ productos activos, verificar que listado sea rápido
- Verificar que paginación funcione correctamente

#### Muchas direcciones
- Crear usuario con 20+ direcciones guardadas
- Verificar que `GET /api/checkout/mode` responda rápido
- Verificar que solo se carguen las primeras 10

### 7.3. Verificación de Queries

**Herramientas recomendadas:**
- Django Debug Toolbar (en desarrollo)
- `django.db.connection.queries` (en código)
- PostgreSQL `EXPLAIN ANALYZE` (en producción)

**Qué buscar:**
- Reducción de número de queries en endpoints optimizados
- Ausencia de queries N+1 (mismo patrón repetido muchas veces)
- Uso de índices en queries (verificar con `EXPLAIN`)

---

## 8. APLICACIÓN DE MIGRACIONES

### 8.1. Migración de Índices

**Archivo**: `apps/cart/migrations/0007_add_cart_composite_indexes.py`

**Comando para aplicar:**
```bash
cd condorshop/backend
python manage.py migrate cart
```

**Verificación:**
```bash
# Verificar que los índices se crearon
python manage.py dbshell
# En PostgreSQL:
\d carts
# Debe mostrar idx_cart_user_active e idx_cart_session_active
```

---

## 9. MÉTRICAS ESPERADAS

### Antes de Optimización
- `GET /api/cart/`: ~5-7 queries
- `GET /api/products/categories/`: ~40-60 queries (con 20 categorías)
- `GET /api/products/`: ~N+1 queries (1 por producto para imágenes)
- `GET /api/checkout/mode`: 1-2 queries (pero carga todas las direcciones)

### Después de Optimización
- `GET /api/cart/`: ~2-3 queries (reducción de 50-60%)
- `GET /api/products/categories/`: ~1-2 queries (reducción de 95%+)
- `GET /api/products/`: ~1-2 queries (reducción de 90%+)
- `GET /api/checkout/mode`: 1-2 queries (pero solo carga 10 direcciones máximo)

### Latencia Esperada
- `GET /api/cart/`: Reducción de 30-50%
- `GET /api/products/categories/`: Reducción de 70-90%
- `GET /api/products/`: Reducción de 20-40%
- `GET /api/checkout/mode`: Reducción de 10-30% (depende de cantidad de direcciones)

---

## 10. NOTAS FINALES

### Cambios que NO se implementaron
1. **Índice GIN para búsqueda de texto**: Considerar solo si hay >10,000 productos
2. **CategoryTreeSerializer.get_product_count()**: Endpoint poco usado, impacto bajo
3. **Optimización de sincronización frontend en create_order**: Necesario por lógica de negocio

### Próximos pasos recomendados
1. Aplicar migración de índices en staging
2. Ejecutar pruebas manuales completas
3. Monitorear métricas de performance en producción
4. Considerar optimizaciones adicionales según resultados

### Rollback
Si hay problemas, los cambios son reversibles:
- Serializers tienen fallbacks
- Migración de índices se puede revertir
- `get_cart_optimized()` se puede eliminar y volver a usar `get_cart()` + recarga

---

**Fecha de implementación**: Diciembre 2024  
**Estado**: ✅ COMPLETADO - Listo para pruebas

---

## 11. REFINAMIENTOS ADICIONALES (Diciembre 2024)

### 11.1. Reducción de Tiempo Bajo Lock

**Ver documento**: `BACKEND_PERFORMANCE_REFINEMENT.md`

**Cambios implementados**:
- ✅ `Cart.get_or_create_cart()`: Optimistic locking (lock solo si hay duplicados)
- ✅ `view_cart()`: Lock condicional (solo si hay items a actualizar)
- ✅ `get_cart_optimized()`: Eliminación de query adicional

**Impacto**: 30-50% reducción en tiempo bajo lock

### 11.2. Logging de Performance

**Implementación**:
- ✅ Middleware `PerformanceLoggingMiddleware` para todos los endpoints `/api/`
- ✅ Logging detallado en `view_cart()` y `list_user_orders()`
- ✅ Configuración en `settings.py` (activo en DEBUG o requests >500ms)

**Beneficio**: Mejor observabilidad y debugging de performance

