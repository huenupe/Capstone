# CondorShop Backend – Documento Técnico

## Stack y arquitectura
- **Framework:** Django 5.2.8 + Django REST Framework 3.16.1  
- **Base de datos:** MySQL (modo `STRICT_TRANS_TABLES`, charset `utf8mb4`)  
- **Autenticación:** `rest_framework_simplejwt` (JWT Bearer) con permisos globales `IsAuthenticatedOrReadOnly`  
- **Aplicaciones clave:**
  - `apps.common`: utilidades compartidas, helpers y management commands (`analyze_indexes`)  
  - `apps.users`: modelo de usuario (`User`), autenticación JWT, direcciones (`Address`) y tokens de reset  
  - `apps.products`: catálogos (`Category`, `Product`, `ProductImage`), filtros y vistas públicas  
  - `apps.cart`: carritos de compra (`Cart`, `CartItem`) para usuarios autenticados o invitados (header `X-Session-Token`)  
  - `apps.orders`: pedidos (`Order`, `OrderItem`, `OrderStatus`, `OrderStatusHistory`) y lógica de checkout  
  - `apps.audit`: middleware para registrar auditorías (crece indefinidamente, pendiente proceso de limpieza)

## Modelos y relaciones destacadas
- **Category**
  - Campos principales: `name`, `slug`, `description`, `image` (`ImageField`, upload `categorias/`)  
  - Índices: `idx_category_slug`  
  - Relaciones: `Product` (`related_name='products'`)  
- **Product**
  - Campos monetarios (`price`, `discount_price`, `discount_amount`) como `PositiveIntegerField` (CLP enteros)  
  - `discount_percent` (`PositiveSmallIntegerField`, 0–100) con `CheckConstraint` (`pct_range_0_100`) y reglas mutuamente excluyentes (`only_one_discount_mode`)  
  - Propiedades: `final_price` (aplica descuentos en orden: precio fijo, monto, % con redondeo entero)  
  - Índices: `idx_product_created_at`, `idx_product_name`, `idx_product_active_created` (combinado `active` + `created_at` para evitar file sort), además de índices por categoría, slug, price, stock  
- **Cart / CartItem**
  - `Cart`: dual (`user` o `session_token`), campos `is_active`, timestamps  
  - `CartItem`: `quantity`, `unit_price`, `total_price` (entero), `UniqueConstraint` (`uq_cartitem_cart_product`)  
  - Índices forzados vía migraciones 0004–0005: `idx_cartitem_cart_product`, `idx_cartitem_product`  
- **Order / OrderItem**
  - `Order`: `status` (FK `OrderStatus`, `on_delete=RESTRICT`), `customer_*`, `shipping_*`, `total_amount`, `shipping_cost` (enteros)  
  - Índice: `idx_order_customer_email`, `idx_orders_user_created`, etc.  
  - `OrderItem`: `unit_price`, `total_price` enteros, FK `product` (`on_delete=RESTRICT`)  
  - `OrderStatusHistory`: traza cambios de estado con `changed_by` opcional  
- **Relaciones clave**
  - `ProductImage` (`ForeignKey` con `on_delete=CASCADE`, `related_name='images'`)  
  - `CartItem` → `Cart` y `Product` (`on_delete=CASCADE`)  
  - `Order` → `User` (`on_delete=SET_NULL`, pedidos invitados), `OrderItem` → `Order` (`CASCADE`)  
  - Todas las FK definen `related_name` explícito y `db_column` snake_case.

## Reglas de negocio relevantes
- Todos los montos se manejan como **enteros en CLP** (sin centavos).  
- `Product.final_price` aplica descuentos priorizando `discount_price` > `discount_amount` > `discount_percent` (redondeo half-up).  
- `CartItem.save()` recalcula `total_price = unit_price * quantity`.  
- `Order.create_order` bloquea inventario con `select_for_update()`, recalcula totales enteros y desactiva el carrito.  
- `evaluate_shipping` (en `apps.orders.services`) devuelve costos enteros, reutilizado para checkout y cotización de envío.

## Endpoints principales
- `/api/products/` (GET): listado con filtros (`category`, `min_price`, `max_price`, `active`, `name__istartswith`, `search`) y orden (`price`, `created_at`).  
- `/api/products/{slug}/` (GET): detalle de producto (imágenes, categoría, precios formateados).  
- `/api/products/categories/` (GET): categorías con imagen.  
- `/api/cart/add` (POST, AllowAny): agrega items; responde `201` y cabecera `X-Session-Token` para invitados.  
- `/api/cart/` (GET): estado del carrito (subtotales, `unit_price`, `subtotal` y totales enteros).  
- `/api/orders/create` (POST): crea pedidos desde el carrito (guest via header `X-Session-Token`, usuarios autenticados). Valida stock y devuelve `OrderSerializer`.  
- `/api/orders/` y `/api/orders/{id}/` (GET, autenticado): historial y detalle de pedidos del usuario.  
- `/api/checkout/shipping-quote` (POST, AllowAny): calcula envío (usa enteros, soporta `subtotal` opcional).  
- `/api/auth/`, `/api/users/`: autenticación JWT y endpoints de usuarios (ver `apps.users.urls`).  
- `/health/`: liveness/readiness (chequeo DB).

## Autenticación y permisos
- JWT Bearer (`Authorization: Bearer <token>`).  
- Permiso global `IsAuthenticatedOrReadOnly`; vistas sensibles sobreescriben:
  - `AllowAny` para registro/login, agregar al carrito e invocar checkout.  
  - `IsAuthenticated` para ver pedidos propios.  
- Rate limiting (`django-ratelimit`) en `shipping_quote` y `create_order`.

## Variables de entorno relevantes
- Base de datos: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.  
- JWT: `JWT_EXPIRATION_HOURS`.  
- Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`.  
- CORS/CSRF: `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.  
- Desarrollo: `DEV_SESSION_COOKIE_AGE`.  
- Opcional Anymail (Mailgun).  
- Logs: se generan en `backend/logs/django.log`.

## Índices y optimizaciones
- **Productos:**  
  - `idx_product_active_created` → filtra `active=1` y utiliza orden natural por `created_at` sin `filesort`.  
  - `idx_product_name` → búsquedas con `name__istartswith`.  
  - `idx_product_created_at`, `idx_product_price`, `idx_product_stock` → reportes y ordenamientos.  
- **Carrito:**  
  - `idx_cartitem_cart_product` + `uq_cartitem_cart_product` → búsquedas por carrito/producto (N+1 evitado).  
  - `idx_cartitem_product` → cálculos por producto.  
- **Pedidos:**  
  - `idx_order_customer_email` → búsqueda directa por correo (checkout invitados).  
- **Notas:** Búsquedas `icontains` siguen sin índice (MySQL no indexa `%term%`); se recomienda `name__istartswith` o evaluar `FULLTEXT` a futuro.

## Comandos de gestión
- `python manage.py analyze_indexes` → ejecuta EXPLAIN (JSON si está disponible) para las consultas críticas e imprime tabla, key, tipo de acceso y notas.  
- `python manage.py load_initial_data` → carga catálogos demo (categorías, productos, usuarios).  
- Scripts auxiliares (`run_server.bat`, `start_backend.bat`) para desarrollo local.  

## Política de migraciones
1. **Pre-check:** `python manage.py makemigrations --dry-run --verbosity 3`, `python manage.py check`.  
2. **Aplicación:** `python manage.py migrate --plan`, luego `python manage.py migrate`.  
3. **Revisión manual:** confirmar archivos generados (nombres e índices explícitos `idx_*`).  
4. **Mantenibilidad:** nuevas migraciones no sustituyen migraciones aplicadas; correcciones históricas se encadenan (ej. `cart` 0004–0005 sincronizan columnas/índices existentes).  
5. **Pruebas:** `pytest -q` obligatorio tras cambios estructurales.

> La migración monetaria de noviembre 2025 convirtió todos los montos a CLP enteros, añadió los índices mencionados y creó el comando `analyze_indexes` para validar su uso.

