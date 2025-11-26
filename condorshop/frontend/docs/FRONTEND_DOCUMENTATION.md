# CondorShop Frontend – Guía Rápida

## Stack
- **Framework:** React + Vite
- **Estado global:** Zustand (`src/store`)
- **HTTP client:** Axios (`src/services/apiClient.js`)
- **Ruteo:** React Router
- **Estilos:** Tailwind + utilidades (ej. `scrollbar-hide` en `src/index.css`)

## Cliente API (`apiClient`)
- Base URL configurable con `VITE_API_URL` (por defecto `http://localhost:8000/api`)
- Inyecta `Authorization: Bearer <token>` si el usuario está autenticado
- Gestiona `X-Session-Token` para carritos de invitados (expone el header en respuestas del backend)
- Maneja errores de red con `console.error` y `toast` en componentes

## Filtros y consultas
- Productos soportan:
  - `category` (ID o slug)
  - `min_price`, `max_price`
  - `active`
  - `name__istartswith=<prefijo>` (uso recomendado para búsquedas rápidas con índice)
  - `search=<texto>` (usa `icontains`, sin índice → para listas cortas)
  - `ordering=price` | `ordering=-created_at`

## Manejo de errores
- Errores funcionales del backend llegan como `{"error": "mensaje"}` y se muestran con `toast.error`
- Validaciones de DRF (400) devuelven diccionarios `{campo: [mensajes]}` que se despliegan cerca de los formularios
- `net::ERR_CONNECTION_REFUSED` y CORS: se escriben en consola y se informan al usuario

## Contrato monetario
- **Todas las cantidades se reciben en enteros CLP.**  
- El formateo (`$19.990`) es responsabilidad del frontend (utilidades en `apps/common/templatetags/currency.py` y helpers JS).
- Los endpoints devuelven: `price`, `discount_price`, `final_price`, `unit_price`, `total_price`, `shipping_cost`, `total_amount`, etc. como enteros.

## Flujos clave
- Carrito invitados:
  1. `POST /api/cart/add` → guardar `X-Session-Token`
  2. `GET /api/cart/` → mostrar totales enteros
  3. `POST /api/orders/create` con header `X-Session-Token`
- Checkout autenticado reutiliza el token JWT y lista pedidos con `/api/orders/`

## Referencias
- Endpoints y ejemplos detallados en [INTEGRATION_CONTRACT.md](../backend/docs/INTEGRATION_CONTRACT.md)
- Resultados de auditoría e índices en [HISTORIAL_DESARROLLO.md](../backend/docs/HISTORIAL_DESARROLLO.md) (Sección 8)

