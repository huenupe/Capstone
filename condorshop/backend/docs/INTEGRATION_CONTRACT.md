# Contrato de Integración – CondorShop API (v1)

## Consideraciones generales
- **Base URL (desarrollo):** `http://localhost:8000/`
- **Autenticación:** JWT (`Authorization: Bearer <token>`). Endpoints públicos indicados abajo aceptan invitados.
- **Moneda:** Todos los montos se retornan como **enteros en CLP**. El frontend formatea (`$19.990`) según su propia lógica.
- **Sesión de carrito invitado:** el backend responde `X-Session-Token`; debe reenviarse en llamadas posteriores.
- **Búsquedas:** para performance se recomienda `name__istartswith=<prefijo>`. `icontains` funciona pero no usa índice.

## Endpoints

### GET /api/products/
Listado paginado (PageNumberPagination – 20 por página).

**Parámetros soportados:**  
`category` (ID o slug), `min_price`, `max_price`, `active`, `name__istartswith`, `search`, `ordering`.

**Respuesta 200**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "name": "Alfombra Índice",
      "price": 25990,
      "discount_price": null,
      "final_price": 25990,
      "discount_percent": 0,
      "calculated_discount_percent": 0,
      "has_discount": false,
      "stock_qty": 20,
      "slug": "alfombra-indice",
      "main_image": null,
      "category": {
        "id": 2,
        "name": "Decoración",
        "slug": "decoracion",
        "description": "Categoría de prueba",
        "image": null
      },
      "price_formatted": "$25.990",
      "final_price_formatted": "$25.990",
      "discount_price_formatted": null
    }
  ]
}
```

### GET /api/products/{slug}/
**Respuesta 200**
```json
{
  "id": 15,
  "name": "Alfombra Índice",
  "slug": "alfombra-indice",
  "description": "Producto de demostración",
  "price": 25990,
  "discount_price": null,
  "final_price": 25990,
  "discount_percent": 0,
  "calculated_discount_percent": 0,
  "has_discount": false,
  "stock_qty": 20,
  "brand": null,
  "sku": "SKU00015",
  "category": {
    "id": 2,
    "name": "Decoración",
    "slug": "decoracion",
    "description": "Categoría de prueba",
    "image": null
  },
  "images": [],
  "created_at": "2025-11-12T02:30:18.315Z",
  "updated_at": "2025-11-12T02:30:18.315Z",
  "price_formatted": "$25.990",
  "final_price_formatted": "$25.990",
  "discount_price_formatted": null
}
```

### POST /api/cart/add
Agrega o incrementa un item. Disponible para invitados y autenticados.

**Request**
```json
{
  "product_id": 15,
  "quantity": 2
}
```

**Response 201**
```json
{
  "message": "Producto agregado al carrito",
  "cart_id": 7
}
```
Headers:
```
X-Session-Token: 5b0f6e5a-18bb-4fc8-8ed5-51e2df70a68c
```

**Errores comunes**
- `400 {"error": "Stock insuficiente. Disponible: 1"}`
- `404 {"error": "Producto no encontrado"}`

### GET /api/cart/
Requiere `X-Session-Token` para invitados o sesión autenticada.

**Response 200**
```json
{
  "id": 7,
  "items": [
    {
      "id": 21,
      "product": {
        "id": 15,
        "name": "Alfombra Índice",
        "price": 25990,
        "discount_price": null,
        "final_price": 25990,
        "discount_percent": 0,
        "calculated_discount_percent": 0,
        "has_discount": false,
        "stock_qty": 20,
        "slug": "alfombra-indice",
        "main_image": null,
        "category": {
          "id": 2,
          "name": "Decoración",
          "slug": "decoracion",
          "description": "Categoría de prueba",
          "image": null
        },
        "price_formatted": "$25.990",
        "final_price_formatted": "$25.990",
        "discount_price_formatted": null
      },
      "quantity": 2,
      "unit_price": 25990,
      "subtotal": 51980,
      "unit_price_formatted": "$25.990",
      "subtotal_formatted": "$51.980"
    }
  ],
  "subtotal": 51980,
  "shipping_cost": 0,
  "total": 51980,
  "subtotal_formatted": "$51.980",
  "shipping_cost_formatted": "$0",
  "total_formatted": "$51.980"
}
```

### POST /api/orders/create
- Autenticados: usa el carrito activo del usuario.
- Invitados: enviar `X-Session-Token` del carrito generado.
- Requiere estado `PENDING` en `OrderStatus` (se crea automáticamente en migraciones).

**Request**
```json
{
  "customer_name": "Demo Customer",
  "customer_email": "demo@example.com",
  "customer_phone": "+56911111111",
  "shipping_street": "Calle Demo 123",
  "shipping_city": "Santiago",
  "shipping_region": "Región Metropolitana",
  "shipping_postal_code": "8320000",
  "save_address": false
}
```

**Response 201**
```json
{
  "id": 11,
  "status": {
    "id": 1,
    "code": "PENDING",
    "description": "Pendiente"
  },
  "customer_name": "Demo Customer",
  "customer_email": "demo@example.com",
  "customer_phone": "+56911111111",
  "shipping_street": "Calle Demo 123",
  "shipping_city": "Santiago",
  "shipping_region": "Región Metropolitana",
  "shipping_postal_code": "8320000",
  "total_amount": 51980,
  "shipping_cost": 0,
  "currency": "CLP",
  "created_at": "2025-11-12T02:45:12.814Z",
  "updated_at": "2025-11-12T02:45:12.814Z",
  "items": [
    {
      "id": 31,
      "product": {
        "id": 15,
        "name": "Alfombra Índice",
        "price": 25990,
        "discount_price": null,
        "final_price": 25990,
        "discount_percent": 0,
        "calculated_discount_percent": 0,
        "has_discount": false,
        "stock_qty": 18,
        "slug": "alfombra-indice",
        "main_image": null,
        "category": {
          "id": 2,
          "name": "Decoración",
          "slug": "decoracion",
          "description": "Categoría de prueba",
          "image": null
        },
        "price_formatted": "$25.990",
        "final_price_formatted": "$25.990",
        "discount_price_formatted": null
      },
      "quantity": 2,
      "unit_price": 25990,
      "total_price": 51980,
      "unit_price_formatted": "$25.990",
      "total_price_formatted": "$51.980"
    }
  ],
  "total_amount_formatted": "$51.980",
  "shipping_cost_formatted": "$0"
}
```

**Errores comunes**
- `400 {"error": "El carrito está vacío"}`
- `400 {"error": "Token de sesión requerido"}` para invitados sin header
- `400 {"error": "Algunos productos del carrito no están disponibles", "missing_product_ids": [15]}`
- `404 {"error": "Carrito no encontrado"}`

### GET /api/orders/{id}/
Autenticado, retorna el pedido perteneciente al usuario.

**Response 200**
```json
{
  "id": 11,
  "status": {
    "id": 1,
    "code": "PENDING",
    "description": "Pendiente"
  },
  "customer_name": "Demo Customer",
  "customer_email": "demo@example.com",
  "customer_phone": "+56911111111",
  "shipping_street": "Calle Demo 123",
  "shipping_city": "Santiago",
  "shipping_region": "Región Metropolitana",
  "shipping_postal_code": "8320000",
  "total_amount": 51980,
  "shipping_cost": 0,
  "currency": "CLP",
  "created_at": "2025-11-12T02:45:12.814Z",
  "updated_at": "2025-11-12T02:45:12.814Z",
  "items": [
    {
      "id": 31,
      "product": {
        "id": 15,
        "name": "Alfombra Índice",
        "price": 25990,
        "discount_price": null,
        "final_price": 25990,
        "discount_percent": 0,
        "calculated_discount_percent": 0,
        "has_discount": false,
        "stock_qty": 18,
        "slug": "alfombra-indice",
        "main_image": null,
        "category": {
          "id": 2,
          "name": "Decoración",
          "slug": "decoracion",
          "description": "Categoría de prueba",
          "image": null
        },
        "price_formatted": "$25.990",
        "final_price_formatted": "$25.990",
        "discount_price_formatted": null
      },
      "quantity": 2,
      "unit_price": 25990,
      "total_price": 51980,
      "unit_price_formatted": "$25.990",
      "total_price_formatted": "$51.980"
    }
  ],
  "total_amount_formatted": "$51.980",
  "shipping_cost_formatted": "$0"
}
```

**Errores**
- `404 {"error": "Pedido no encontrado"}` si el pedido no pertenece al usuario.

## Duplicidad de validaciones
- **Frontend UX:** mensajes inmediatos (campos vacíos, formato de correo) para mejorar usabilidad.
- **Backend:** validación definitiva (stock, cohorte de descuentos, token de sesión, autenticación). Ante discrepancias siempre prevalece la respuesta del backend.

## Changelog reciente
- **11-2025:** migración completa a CLP enteros, indices optimizados (`idx_product_active_created`, `idx_cartitem_*`, `idx_order_customer_email`), comando `analyze_indexes`, filtro rápido `name__istartswith`.

> Para resultados actualizados del EXPLAIN consulta [AUDIT_REPORT.md](AUDIT_REPORT.md).

