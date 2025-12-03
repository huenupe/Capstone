# 🔍 Análisis de Performance Frontend - CondorShop

**Fecha**: Diciembre 2024  
**Objetivo**: Identificar y eliminar llamadas duplicadas/innecesarias a API, mejorar percepción de fluidez

---

## 1. MAPEO DE LLAMADAS A LA API

### 1.1. GET /api/cart/

| Archivo | Componente/Hook | Momento de Disparo | Dependencias | Estado |
|---------|----------------|-------------------|--------------|--------|
| `pages/Cart.jsx:48` | `loadCart()` | `useEffect` al montar | `[loadCart]` | ❌ PROBLEMA: Se ejecuta 2 veces (StrictMode) |
| `pages/Cart.jsx:67` | `loadCart()` | `useEffect` cuando `isAuthenticated` cambia | `[isAuthenticated, loadCart]` | ⚠️ Puede causar doble llamada |
| `pages/Cart.jsx:97` | `loadCart()` | Después de `updateCartItem()` exitoso | Click en botón +/- | ❌ INNECESARIO: Ya tenemos respuesta |
| `pages/Cart.jsx:110` | `loadCart()` | Después de error en `updateCartItem()` | Error handler | ✅ Necesario (sincronización) |
| `pages/Cart.jsx:152` | `loadCart()` | Después de error en `removeCartItem()` | Error handler | ✅ Necesario (sincronización) |
| `pages/ProductDetail.jsx:60` | `cartService.getCart()` | Después de `addToCart()` exitoso | Click en "Agregar al carrito" | ❌ INNECESARIO: Backend ya actualiza |
| `pages/ProductDetail.jsx:74` | `cartService.getCart()` | Después de error en `addToCart()` | Error handler | ✅ Necesario (sincronización) |
| `components/home/ProductRail.jsx:53` | `cartService.getCart()` | Después de `addToCart()` exitoso | Click en "Agregar al carrito" | ❌ INNECESARIO: Backend ya actualiza |
| `components/home/ProductRail.jsx:67` | `cartService.getCart()` | Después de error en `addToCart()` | Error handler | ✅ Necesario (sincronización) |
| `pages/CategoryPage.jsx:238` | `cartService.getCart()` | Después de `addToCart()` exitoso | Click en "Agregar al carrito" | ❌ INNECESARIO: Backend ya actualiza |
| `pages/CategoryPage.jsx:247` | `cartService.getCart()` | Después de error en `addToCart()` | Error handler | ✅ Necesario (sincronización) |
| `pages/Auth/Login.jsx:42` | `cartService.getCart()` | Después de login exitoso | Login handler | ✅ Necesario (sincronizar carrito) |

**Total de llamadas a GET /api/cart/**: 
- **Al entrar a Cart**: 1-2 (por StrictMode y useEffect duplicado)
- **Al hacer click +/-**: 2 (optimistic update + refetch innecesario)
- **Al agregar producto**: 2 (addToCart + getCart innecesario)

### 1.2. POST /api/cart/add

| Archivo | Componente/Hook | Momento de Disparo | Dependencias | Estado |
|---------|----------------|-------------------|--------------|--------|
| `pages/ProductDetail.jsx:53` | `cartService.addToCart()` | Click en "Agregar al carrito" | Click handler | ✅ Correcto |
| `components/home/ProductRail.jsx:46` | `cartService.addToCart()` | Click en "Agregar al carrito" | Click handler | ✅ Correcto |
| `pages/CategoryPage.jsx:232` | `cartService.addToCart()` | Click en "Agregar al carrito" | Click handler | ✅ Correcto |

**Total**: 3 lugares, todos correctos

### 1.3. PATCH /api/cart/items/{id}

| Archivo | Componente/Hook | Momento de Disparo | Dependencias | Estado |
|---------|----------------|-------------------|--------------|--------|
| `pages/Cart.jsx:93` | `cartService.updateCartItem()` | Click en botón +/- | `handleUpdateQuantity()` | ✅ Correcto |
| `pages/Cart.jsx:97` | `loadCart()` después | Después de update exitoso | Success handler | ❌ INNECESARIO |

**Problema**: Después de cada click en +/-, se hace:
1. Optimistic update (correcto)
2. PATCH request (correcto)
3. GET /api/cart/ completo (❌ INNECESARIO)

### 1.4. DELETE /api/cart/items/{id}/delete

| Archivo | Componente/Hook | Momento de Disparo | Dependencias | Estado |
|---------|----------------|-------------------|--------------|--------|
| `pages/Cart.jsx:139` | `cartService.removeCartItem()` | Click en botón eliminar | `handleRemoveItem()` | ✅ Correcto |
| `pages/Cart.jsx:152` | `loadCart()` después | Solo en caso de error | Error handler | ✅ Necesario |

**Estado**: Correcto (solo recarga en error)

### 1.5. GET /api/orders/

| Archivo | Componente/Hook | Momento de Disparo | Dependencias | Estado |
|---------|----------------|-------------------|--------------|--------|
| `pages/Orders.jsx:33` | `ordersService.getUserOrders()` | `useEffect` al montar | `[loadOrders]` | ⚠️ Puede ejecutarse 2 veces (StrictMode) |
| `pages/Orders.jsx:117` | `loadOrders()` | Después de cancelar orden | Success handler | ✅ Necesario |
| `components/profile/OrderHistory.jsx:33` | `ordersService.getUserOrders()` | `useEffect` al montar | `[loadOrders]` | ⚠️ Puede ejecutarse 2 veces (StrictMode) |

**Problema**: 
- `Orders.jsx` y `OrderHistory.jsx` hacen la misma llamada (duplicado si ambos se montan)
- StrictMode causa doble ejecución en desarrollo

---

## 2. DETECCIÓN DE PROBLEMAS

### 2.1. Llamadas Duplicadas / Overfetching

#### ❌ PROBLEMA 1: React.StrictMode causa dobles renders
**Ubicación**: `main.jsx:27`

```jsx
<React.StrictMode>
  <App />
</React.StrictMode>
```

**Impacto**:
- En desarrollo, todos los `useEffect` se ejecutan 2 veces
- Esto causa 2 llamadas a `GET /api/cart/` al montar `Cart.jsx`
- Esto causa 2 llamadas a `GET /api/orders/` al montar `Orders.jsx`

**Solución**: Proteger `useEffect` con flags o usar `useRef` para evitar dobles ejecuciones

#### ❌ PROBLEMA 2: Cart.jsx - loadCart() después de updateCartItem()
**Ubicación**: `pages/Cart.jsx:97`

```javascript
await cartService.updateCartItem(itemId, { quantity })
// ❌ INNECESARIO: Recargar carrito completo después de actualizar
await loadCart()
```

**Impacto**:
- Cada click en +/- causa 2 requests: PATCH + GET
- Si el usuario hace 5 clicks rápidos → 10 requests

**Solución**: 
- Usar respuesta del PATCH si trae datos actualizados
- O actualizar estado optimista sin refetch

#### ❌ PROBLEMA 3: Múltiples getCart() después de addToCart()
**Ubicaciones**: 
- `ProductDetail.jsx:60`
- `ProductRail.jsx:53`
- `CategoryPage.jsx:238`

**Impacto**:
- Cada "Agregar al carrito" causa 2 requests: POST + GET
- Si el usuario agrega 3 productos → 6 requests

**Solución**: 
- Backend ya actualiza el carrito en `addToCart()`
- No necesitamos refetch si hacemos optimistic update correcto

#### ⚠️ PROBLEMA 4: Cart.jsx - useEffect duplicado
**Ubicación**: `pages/Cart.jsx:58-69`

```javascript
useEffect(() => {
  loadCart()  // Primera llamada
}, [loadCart])

useEffect(() => {
  if (isAuthenticated) {
    loadCart()  // Segunda llamada si está autenticado
  }
}, [isAuthenticated, loadCart])
```

**Impacto**:
- Si el usuario está autenticado, se hacen 2 llamadas al montar
- Con StrictMode → 4 llamadas en desarrollo

**Solución**: Combinar en un solo `useEffect` con lógica condicional

#### ⚠️ PROBLEMA 5: Orders.jsx y OrderHistory.jsx duplicados
**Ubicaciones**: 
- `pages/Orders.jsx:33`
- `components/profile/OrderHistory.jsx:33`

**Impacto**:
- Si ambos componentes se montan, se hacen 2 llamadas a `/api/orders/`
- Con StrictMode → 4 llamadas en desarrollo

**Solución**: Centralizar en un store o hook compartido

---

## 3. ANÁLISIS DEL STORE ACTUAL (Zustand)

### 3.1. cartSlice.js - Estado Actual

**Fortalezas**:
- ✅ Ya usa Zustand con persist
- ✅ Tiene métodos `addItem`, `updateItemQuantity`, `removeItem`
- ✅ Calcula valores derivados automáticamente
- ✅ Solo persiste `items` (optimizado)

**Debilidades**:
- ❌ No tiene método `fetchCart()` centralizado
- ❌ No tiene protección contra múltiples fetches simultáneos
- ❌ No tiene estado de loading/error
- ❌ No tiene optimistic updates integrados con API

**Problema**: Cada componente hace su propio `cartService.getCart()` y luego `setCart()`, sin coordinación.

---

## 4. PLAN DE OPTIMIZACIÓN

### 4.1. Centralizar y Cachear Estado del Carrito

**Objetivo**: Un solo lugar para fetch del carrito, con protección contra múltiples llamadas simultáneas.

**Cambios propuestos**:

1. **Añadir al store**:
   - `fetchCart()`: Método centralizado con protección
   - `isLoading`: Estado de carga
   - `lastFetched`: Timestamp del último fetch
   - `fetchInProgress`: Flag para evitar múltiples fetches simultáneos

2. **Protección contra dobles ejecuciones**:
   - Usar `useRef` para flags en componentes
   - O mejor: mover toda la lógica al store

### 4.2. Optimistic UI en Acciones de Carrito

**Objetivo**: UI responde al instante, API se sincroniza en background.

**Cambios propuestos**:

1. **addToCart()**:
   - Actualizar store inmediatamente (optimistic)
   - Lanzar POST en background
   - Si falla, revertir y mostrar error
   - NO hacer GET después (confiar en optimistic update)

2. **updateCartItem()**:
   - Actualizar store inmediatamente (optimistic)
   - Lanzar PATCH en background
   - Si falla, revertir y mostrar error
   - NO hacer GET después (usar respuesta del PATCH si trae datos)

3. **removeCartItem()**:
   - Ya está bien implementado (optimistic + DELETE)
   - Solo recargar en caso de error

### 4.3. Eliminar Llamadas Innecesarias

**Cambios propuestos**:

1. **Cart.jsx**:
   - Eliminar `loadCart()` después de `updateCartItem()` exitoso
   - Combinar `useEffect` duplicados
   - Proteger contra StrictMode

2. **ProductDetail.jsx, ProductRail.jsx, CategoryPage.jsx**:
   - Eliminar `getCart()` después de `addToCart()` exitoso
   - Usar optimistic update del store

3. **Login.jsx**:
   - Mantener `getCart()` (necesario para sincronizar)

### 4.4. Optimización de /api/orders/

**Cambios propuestos**:

1. **Centralizar en store o hook**:
   - Crear `useOrders()` hook o añadir al store
   - Proteger contra múltiples fetches

2. **Skeleton/Loader**:
   - Mostrar skeleton mientras carga
   - Mejorar percepción de fluidez

3. **Evitar duplicación**:
   - Si `Orders.jsx` y `OrderHistory.jsx` se usan juntos, compartir estado

### 4.5. Protección contra React.StrictMode

**Cambios propuestos**:

1. **Usar `useRef` para flags**:
   ```javascript
   const hasFetched = useRef(false)
   useEffect(() => {
     if (hasFetched.current) return
     hasFetched.current = true
     loadCart()
   }, [])
   ```

2. **O mejor: usar AbortController**:
   ```javascript
   useEffect(() => {
     const abortController = new AbortController()
     loadCart(abortController.signal)
     return () => abortController.abort()
   }, [])
   ```

---

## 5. CAMBIOS CONCRETOS PROPUESTOS

### Cambio 1: Mejorar cartSlice.js con fetchCart() centralizado

**Archivo**: `store/cartSlice.js`

**Añadir**:
- `isLoading: false`
- `fetchInProgress: false`
- `fetchCart()`: Método centralizado con protección
- `syncCart()`: Sincronizar con API cuando sea necesario

### Cambio 2: Optimizar Cart.jsx

**Archivo**: `pages/Cart.jsx`

**Eliminar**:
- `loadCart()` después de `updateCartItem()` exitoso (línea 97)
- `useEffect` duplicado (combinar en uno)

**Añadir**:
- Protección contra StrictMode
- Usar `fetchCart()` del store en lugar de `loadCart()` local

### Cambio 3: Optimizar ProductDetail.jsx, ProductRail.jsx, CategoryPage.jsx

**Eliminar**:
- `getCart()` después de `addToCart()` exitoso

**Añadir**:
- Optimistic update del store antes de llamar API
- Revertir si falla

### Cambio 4: Crear hook useOrders() o añadir al store

**Archivo**: `hooks/useOrders.js` (nuevo) o `store/ordersSlice.js` (nuevo)

**Funcionalidad**:
- Fetch centralizado
- Protección contra múltiples llamadas
- Estado de loading/error

### Cambio 5: Añadir Skeleton para Orders

**Archivo**: `pages/Orders.jsx`

**Añadir**:
- Componente Skeleton mientras carga
- Mejorar percepción de fluidez

---

## 6. MEDICIÓN Y VERIFICACIÓN

### 6.1. Logging en Desarrollo

**Añadir en servicios**:

```javascript
// services/cart.js
export const cartService = {
  getCart: async () => {
    if (import.meta.env.DEV) {
      console.time('GET /api/cart/')
    }
    const response = await apiClient.get('/cart/')
    if (import.meta.env.DEV) {
      console.timeEnd('GET /api/cart/')
      console.log('Cart data:', response.data)
    }
    return response.data
  },
  // ... más métodos
}
```

### 6.2. Verificación en Network Tab

**Antes de optimización**:
- Al entrar a Cart: 2-4 requests a GET /api/cart/ (StrictMode + useEffect duplicado)
- Al hacer click +/-: 2 requests (PATCH + GET)
- Al agregar producto: 2 requests (POST + GET)

**Después de optimización**:
- Al entrar a Cart: 1 request a GET /api/cart/
- Al hacer click +/-: 1 request (solo PATCH)
- Al agregar producto: 1 request (solo POST)

---

## 7. RIESGOS Y MITIGACIONES

### Riesgo Alto
- Ninguno identificado

### Riesgo Medio
- **Optimistic updates**: Si falla la API, el estado puede quedar inconsistente
  - **Mitigación**: Siempre revertir en caso de error y mostrar mensaje claro

- **Eliminar refetch después de updateCartItem()**: Puede perder sincronización si el backend actualiza algo más
  - **Mitigación**: Usar respuesta del PATCH si trae datos, o hacer refetch solo en casos específicos

### Riesgo Bajo
- Todos los demás cambios tienen fallbacks o no cambian lógica funcional

---

## 8. RESUMEN DE PROBLEMAS DETECTADOS

| Problema | Severidad | Impacto | Ubicación |
|----------|-----------|---------|-----------|
| React.StrictMode causa dobles renders | Alta | 2x requests en desarrollo | `main.jsx:27` |
| loadCart() después de updateCartItem() | Alta | 2 requests por click +/- | `Cart.jsx:97` |
| getCart() después de addToCart() | Alta | 2 requests por "Agregar" | Múltiples archivos |
| useEffect duplicado en Cart.jsx | Media | 2 llamadas al montar | `Cart.jsx:58-69` |
| Orders.jsx y OrderHistory.jsx duplicados | Media | 2 llamadas si ambos montan | Ambos archivos |
| Falta skeleton en Orders | Baja | Percepción de lentitud | `Orders.jsx` |

---

## 9. PRÓXIMOS PASOS

1. ✅ Crear análisis completo (este documento)
2. ⏳ Implementar optimizaciones propuestas
3. ⏳ Añadir logging de medición
4. ⏳ Verificar en Network tab
5. ⏳ Documentar cambios

