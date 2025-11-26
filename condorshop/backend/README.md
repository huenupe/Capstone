# CondorShop - Backend API

Backend Django 5.2.8 con Django REST Framework 3.16.1 para plataforma e-commerce académica. Integración completa con Webpay Plus (Transbank) para procesamiento de pagos. Base de datos PostgreSQL con soporte para Supabase.

**Última actualización:** Noviembre 2025

## ⚡ Inicio Rápido

### Comando Simplificado

Desde el directorio raíz del proyecto:

```powershell
cd backend
python manage.py runserver
```

**¡Eso es todo!** El script `manage.py` automáticamente detectará y usará el entorno virtual local.

## 📋 Requisitos

- **Python**: 3.11+ (recomendado: 3.12)
- **PostgreSQL**: 12+ (o Supabase)
- **pip**: Última versión
- **setuptools**: Requerido para Python 3.12+ (transbank-sdk depende de distutils)

## 🛠️ Stack Tecnológico

### Core
- **Django**: 5.2.8
- **Django REST Framework**: 3.16.1
- **PostgreSQL**: 12+ (psycopg2-binary 2.9.9)

### Autenticación y Seguridad
- **djangorestframework-simplejwt**: 5.5.1 (JWT tokens)
- **django-cors-headers**: 4.9.0 (CORS)
- **django-ratelimit**: 4.1.0 (Rate limiting)

### Utilidades
- **django-filter**: 25.2 (Filtros avanzados)
- **django-environ**: 0.12.0 (Variables de entorno)
- **Pillow**: 11.0.0 (Procesamiento de imágenes)

### Pagos
- **transbank-sdk**: 3.0.0 (Webpay Plus)

### Testing
- **pytest**: 8.4.2
- **pytest-django**: 4.11.1
- **pytest-cov**: 7.0.0
- **factory-boy**: 3.3.0

## 🚀 Instalación

### Primera Vez - Instalación Completa

1. **Crear un entorno virtual:**
```bash
cd backend
python -m venv .venv
```

2. **Instalar dependencias:**
```bash
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# O en Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
```

**Nota:** El proyecto usa `.venv` como entorno virtual oficial. El repositorio ignora y no versiona ningún entorno virtual.

3. **Configurar variables de entorno:**
```bash
# Copiar archivo de ejemplo
copy .env.example .env  # Windows
# cp .env.example .env   # Linux/Mac

# Editar .env con tus credenciales
```

4. **Crear la base de datos PostgreSQL:**
```sql
CREATE DATABASE condorshop;
```

O si usas Supabase, crear el proyecto y obtener las credenciales de conexión.

5. **Ejecutar migraciones:**
```bash
python manage.py migrate
```

6. **Crear superusuario (opcional):**
```bash
python manage.py createsuperuser
```

7. **Cargar datos iniciales (opcional):**
```bash
python manage.py load_initial_data
```

### Inicio del Servidor

Después de la instalación inicial, simplemente ejecuta:

```bash
cd backend
python manage.py runserver
```

El servidor estará disponible en: http://127.0.0.1:8000/

## 🔧 Variables de Entorno

El archivo `.env` debe contener las siguientes variables:

### Requeridas

- `SECRET_KEY`: Clave secreta de Django (generar una única con al menos 50 caracteres)
- `DEBUG`: `True` para desarrollo, `False` para producción
- `DB_NAME`: Nombre de la base de datos PostgreSQL
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `DB_HOST`: Host de PostgreSQL (default: `localhost`, para Supabase: `db.xxxxx.supabase.co`)
- `DB_PORT`: Puerto de PostgreSQL (default: `5432`)

### Opcionales

- `ALLOWED_HOSTS`: Lista de hosts permitidos separados por comas (default: `localhost,127.0.0.1`)
- `CORS_ALLOWED_ORIGINS`: URLs del frontend separadas por comas (default: `http://localhost:5173,http://127.0.0.1:5173`)
- `CSRF_TRUSTED_ORIGINS`: URLs confiables para CSRF (default: igual que CORS)
- `JWT_EXPIRATION_HOURS`: Horas de expiración del token JWT (default: `24`)
- `EMAIL_BACKEND`: Backend de email (default: `django.core.mail.backends.console.EmailBackend`)
- `FRONTEND_RESET_URL`: URL del frontend para reset de contraseña (default: `http://localhost:5173/reset-password`)
- `PASSWORD_RESET_TIMEOUT_HOURS`: Horas de validez del token de reset (default: `1`)

### Webpay Plus (Transbank)

**⚠️ IMPORTANTE:** Estas variables son requeridas para procesar pagos reales. Para desarrollo/testing, se usan valores por defecto de integración.

- `WEBPAY_ENVIRONMENT`: Ambiente de Webpay (`integration` para testing, `production` para producción)
- `WEBPAY_COMMERCE_CODE`: Código de comercio de Transbank (default en integración: `597055555532`)
- `WEBPAY_API_KEY`: API Key de Transbank (default en integración: `579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C`)
- `WEBPAY_RETURN_URL`: URL de callback de Webpay (default: `http://localhost:8000/api/payments/return/`)
- `WEBPAY_FINAL_URL`: URL final después del pago (default: `http://localhost:5173/payment/result`)

**Nota:** En producción, `WEBPAY_RETURN_URL` y `WEBPAY_FINAL_URL` NO pueden usar `localhost`. Deben ser URLs públicas accesibles desde internet.

### Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**⚠️ IMPORTANTE:** Nunca compartas tu `SECRET_KEY` ni la subas a control de versiones.

## ✨ Funcionalidades Principales

### Catálogo y Productos
- ✅ Listado paginado de productos (20 por página)
- ✅ Búsqueda avanzada (`name__istartswith` con índice, `search` con `icontains`)
- ✅ Filtros por categoría, rango de precios, estado activo
- ✅ Ordenamiento por precio, fecha de creación
- ✅ Categorías con jerarquía (parent/child)
- ✅ Historial automático de precios (signals)
- ✅ Control de inventario con reservas y liberaciones

### Carrito de Compras
- ✅ Carrito para usuarios autenticados
- ✅ Carrito para invitados (con `X-Session-Token`)
- ✅ Fusión automática al autenticarse
- ✅ Validación de stock en tiempo real
- ✅ Precios fijados al agregar al carrito

### Checkout y Pedidos
- ✅ Checkout multipaso (usuario autenticado e invitado)
- ✅ Cotización de envío en tiempo real
- ✅ Snapshots de productos y envío (preservan datos históricos)
- ✅ Validación transaccional de stock (`select_for_update()`)
- ✅ Estados de pedido: PENDING, PAID, FAILED, CANCELLED, PREPARING, SHIPPED, DELIVERED
- ✅ Cancelación de pedidos pendientes

### Pagos Webpay Plus
- ✅ Integración completa con Transbank Webpay Plus
- ✅ Creación y confirmación de transacciones
- ✅ Manejo de callbacks de Webpay
- ✅ Prevención de duplicados (constraint único + verificación proactiva)
- ✅ Registro completo de transacciones (PaymentTransaction)

### Autenticación y Usuarios
- ✅ Registro y login con JWT
- ✅ Recuperación de contraseña (email con token)
- ✅ Perfil de usuario editable
- ✅ Gestión de direcciones (CRUD)
- ✅ Roles: cliente y admin

### Sistema de Envíos
- ✅ Reglas de envío por producto, categoría o general
- ✅ Zonas de envío (regiones)
- ✅ Cálculo de costos de envío
- ✅ Envío gratis configurable (umbral en `StoreConfig`)

### Auditoría
- ✅ Registro automático de acciones (middleware)
- ✅ Logs de cambios en modelos críticos

## Estructura del Proyecto

```
backend/
├── condorshop_api/     # Configuración del proyecto
├── apps/
│   ├── common/         # Utilidades compartidas (Currency, StoreConfig)
│   ├── users/          # Usuarios, autenticación, direcciones
│   ├── products/       # Catálogo de productos, categorías
│   ├── cart/           # Carrito de compras (usuarios y sesiones)
│   ├── orders/         # Pedidos, pagos, envíos, Webpay
│   └── audit/          # Sistema de auditoría automática
└── media/              # Archivos multimedia
```

### Apps y Responsabilidades

- **`apps.common`**: Utilidades compartidas, configuración global (`StoreConfig`), helpers de formato
- **`apps.users`**: Modelo de usuario personalizado, autenticación JWT, recuperación de contraseña, gestión de direcciones
- **`apps.products`**: Productos, categorías (con jerarquía), imágenes, historial de precios, control de inventario
- **`apps.cart`**: Carritos de compra para usuarios autenticados e invitados (con `X-Session-Token`)
- **`apps.orders`**: Pedidos, estados, snapshots, reglas de envío, integración Webpay Plus
- **`apps.audit`**: Registro automático de acciones mediante middleware

## 📡 Endpoints de la API

### Versionado de la API

Actualmente todos los endpoints viven bajo el prefijo `/api/` (sin número de versión). Para el lanzamiento en producción se recomienda introducir un prefijo `/api/v1/` y mantener este README actualizado cuando se realice el corte de versión.

### Autenticación (`/api/auth/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/api/auth/register` | Registro de nuevo cliente | `AllowAny` |
| POST | `/api/auth/login` | Login de usuario (retorna JWT) | `AllowAny` |
| POST | `/api/auth/token/` | Obtener token JWT (SimpleJWT) | `AllowAny` |
| POST | `/api/auth/token/refresh/` | Refrescar token JWT | `AllowAny` |
| POST | `/api/auth/forgot-password` | Solicitar recuperación de contraseña (siempre responde 200) | `AllowAny` |
| POST | `/api/auth/reset-password` | Restablecer contraseña con un token válido | `AllowAny` |
| GET | `/api/auth/verify-reset-token/{token}/` | Verificar si el token es válido antes de mostrar el formulario | `AllowAny` |

**Ejemplo de respuesta de login:**
```json
{
  "user": {
    "id": 1,
    "email": "usuario@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "client"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### Recuperación de contraseña

- Los tokens expiran según `PASSWORD_RESET_TIMEOUT_HOURS` (por defecto, 1 hora).
- El enlace enviado apunta al frontend (`FRONTEND_RESET_URL`) e incluye el token como querystring.
- Las solicitudes y confirmaciones quedan registradas en auditoría cuando el módulo está disponible.

### Usuarios (`/api/users/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET/PATCH | `/api/users/profile` | Ver/editar perfil de usuario | `IsAuthenticated` |
| DELETE | `/api/users/me` | Desactivar cuenta del usuario autenticado | `IsAuthenticated` |
| GET | `/api/users/addresses` | Listar direcciones del usuario | `IsAuthenticated` |
| POST | `/api/users/addresses` | Crear nueva dirección | `IsAuthenticated` |
| GET | `/api/users/addresses/{id}` | Obtener detalle de dirección | `IsAuthenticated` |
| PATCH | `/api/users/addresses/{id}` | Actualizar dirección | `IsAuthenticated` |
| DELETE | `/api/users/addresses/{id}` | Eliminar dirección | `IsAuthenticated` |

### Productos (`/api/products/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/products/` | Listado con paginación, búsqueda, filtros | `IsAuthenticatedOrReadOnly` |
| GET | `/api/products/{slug}/` | Detalle de producto | `IsAuthenticatedOrReadOnly` |
| GET | `/api/products/categories/` | Listado de categorías | `IsAuthenticatedOrReadOnly` |
| GET | `/api/products/{slug}/price-history/` | Historial de precios del producto | `IsAuthenticatedOrReadOnly` |

**Parámetros de consulta:**
- `search`: Búsqueda en nombre y descripción
- `category`: Filtrar por categoría
- `min_price`, `max_price`: Rango de precios
- `ordering`: Ordenar por (`price`, `-price`, `created_at`, `-created_at`)
- `page`: Número de página (paginación)

**Paginación:** La API utiliza `PageNumberPagination` con un `PAGE_SIZE` por defecto de **20** elementos. Las respuestas tienen la estructura:

```json
{
  "count": 40,
  "next": "http://localhost:8000/api/products/?page=3",
  "previous": "http://localhost:8000/api/products/?page=1",
  "results": [ /* productos */ ]
}
```

Puedes solicitar un tamaño de página distinto con `page_size` (máximo 100).

**Imágenes de productos:** El detalle `/api/products/{slug}/` incluye el arreglo `images` ordenado por `position` con los campos `id`, `url`, `image` (URL absoluta), `alt_text` y `position`. El listado expone `main_image` ya normalizado.

### Carrito (`/api/cart/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/cart/` | Ver carrito actual | `AllowAny` |
| POST | `/api/cart/add` | Agregar producto al carrito | `AllowAny` |
| PATCH | `/api/cart/items/{id}` | Actualizar cantidad de item | `AllowAny` |
| DELETE | `/api/cart/items/{id}/delete` | Eliminar item del carrito | `AllowAny` |

**Flujo de invitados:** Si la petición llega sin autenticación, el backend genera automáticamente un `X-Session-Token`, lo devuelve en los headers de la respuesta y lo reutiliza para enlazar el carrito invitado entre solicitudes. El frontend solo debe reenviar ese header en peticiones subsecuentes; si el token no se entrega, el backend emitirá uno nuevo.

**Handshake recomendado para invitados:**
1. El frontend llama a `POST /api/cart/add` sin autenticarse.
2. El backend responde con `X-Session-Token` y un carrito asociado.
3. El frontend persiste ese token (por ejemplo en `localStorage`) y lo reenvía en todos los requests del carrito y el checkout.
4. Si el invitado se autentica posteriormente, el carrito se fusionará al usuario en la siguiente interacción.

### Checkout y Pedidos

El módulo de órdenes expone los mismos endpoints bajo dos prefijos por conveniencia:
- `/api/checkout/` pensado para el flujo público (clientes e invitados).
- `/api/orders/` para historial y detalle de órdenes autenticadas.

#### Checkout público (`/api/checkout/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/checkout/mode` | Información del modo de checkout (detecta direcciones guardadas) | `IsAuthenticatedOrReadOnly` |
| POST | `/api/checkout/shipping-quote` | Cotizar envío para una región y los ítems del carrito | `AllowAny` |
| POST | `/api/checkout/create` *(alias de `/api/orders/create`)* | Crear pedido desde el carrito (clientes o invitados) | `AllowAny` |

#### Historial autenticado (`/api/orders/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/orders/` | Historial de pedidos del usuario autenticado | `IsAuthenticated` |
| GET | `/api/orders/{id}/` | Detalle de un pedido del usuario | `IsAuthenticated` |
| POST | `/api/orders/{id}/pay/` | Iniciar pago Webpay para una orden | `IsAuthenticated` |
| POST | `/api/orders/{id}/cancel/` | Cancelar un pedido pendiente | `IsAuthenticated` |

#### Pagos / Webpay Plus

**✅ INTEGRACIÓN COMPLETA Y FUNCIONAL**

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/api/checkout/{order_id}/pay/` o `/api/orders/{order_id}/pay/` | Iniciar transacción de pago Webpay | `IsAuthenticated` |
| GET/POST | `/api/payments/return/` | Callback de retorno de Webpay (llamado por Transbank) | `AllowAny` |
| GET | `/api/payments/status/{order_id}/` | Consultar estado de pago de una orden | `IsAuthenticated` |

**Flujo completo de pago:**

1. **Crear orden:** `POST /api/checkout/create` → Retorna `order_id`
2. **Iniciar pago:** `POST /api/orders/{order_id}/pay/` → Retorna `{ token, url, buy_order }`
3. **Redirigir a Webpay:** Frontend redirige al usuario a `url` con `token_ws`
4. **Usuario paga en Webpay:** Transbank procesa el pago
5. **Callback:** Webpay llama a `/api/payments/return/?token_ws=XXX`
6. **Confirmación:** Backend confirma la transacción y actualiza el estado de la orden
7. **Redirección:** Usuario es redirigido a `WEBPAY_FINAL_URL` con parámetros de estado
8. **Verificación:** Frontend puede consultar `/api/payments/status/{order_id}/` para obtener detalles completos

**Formato del buy_order:**
- Máximo 26 caracteres (límite de Transbank)
- Formato: `ORD-{order_id}-{timestamp_compact}`
- Incluye microsegundos para garantizar unicidad
- Verificación proactiva de duplicados antes de crear transacción
- Constraint único en base de datos (migración 0013)

**Ejemplo de respuesta de iniciar pago:**
```json
{
  "token": "01ab37d5090650ad055fed59e5e92224c2598883ef40656744...",
  "url": "https://webpay3gint.transbank.cl/webpayserver/initTransaction",
  "buy_order": "ORD-1-251118234635443",
  "order_id": 1,
  "amount": 112471
}
```

**Ejemplo de respuesta de estado de pago:**
```json
{
  "order_id": 1,
  "order_status": "PAID",
  "order_status_name": "Pagado",
  "amount": 112471,
  "currency": "CLP",
  "transaction_data": {
    "authorization_code": "123456",
    "transaction_date": "2025-11-18T23:46:35Z",
    "card_brand": "VISA",
    "card_last_four": "1234",
    "installments_number": 1
  },
  "items": [
    {
      "name": "Producto Ejemplo",
      "quantity": 2,
      "total_price": 112471
    }
  ]
}
```

**⚠️ IMPORTANTE - localhost funciona:**
- ✅ La integración Webpay Plus funciona correctamente con `localhost:8000` y `localhost:5173` en desarrollo
- ✅ No es necesario usar `ngrok` u otras herramientas de tunneling para desarrollo
- ✅ En producción, `WEBPAY_RETURN_URL` y `WEBPAY_FINAL_URL` deben ser URLs públicas

**Tarjetas de prueba (ambiente integración):**
- **Aprobar:** 4051885600446623 (cualquier CVV, fecha futura)
- **Rechazar:** 4051885600446624 (cualquier CVV, fecha futura)

### Administración

Toda la gestión interna se realiza desde el panel nativo de Django disponible en `/admin/`.  
Los usuarios con rol `admin` pueden crear y editar productos, revisar pedidos, actualizar estados y gestionar el contenido directamente desde esa interfaz sin recurrir a endpoints REST específicos.

## 📥 Formato de respuestas y errores

- **Éxito (2xx):** Los endpoints retornan payloads JSON consistentes con los serializers correspondientes.
- **Errores de validación (400):** DRF responde como `{ "campo": ["mensaje"] }`.
- **Errores de negocio (400/404):** Se devuelven como `{ "error": "mensaje descriptivo" }` (por ejemplo, `{"error": "Stock insuficiente"}`). Estamos migrando gradualmente a `detail`, pero este formato se mantiene para compatibilidad.
- **Autenticación (401) / Autorización (403) / Rate limiting (429):** DRF responde con `{ "detail": "..." }` (por ejemplo, `{"detail": "Request was throttled."}`).

Los encabezados relevantes (`X-Session-Token`, `Set-Cookie`, etc.) se exponen directamente; recuerda leer `X-Session-Token` cuando operes como invitado.

## 🔐 Autenticación JWT

El backend usa JWT (JSON Web Tokens) para autenticación. Después de hacer login o registro, recibirás un token `access` y un token `refresh`.

### Uso del Token

Incluir el token en todas las peticiones protegidas:

```http
Authorization: Bearer <access_token>
```

### Refrescar Token

Cuando el token `access` expire, usar el token `refresh` para obtener uno nuevo:

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Configuración de Tokens

- **Access Token:** Expira en 24 horas (configurable con `JWT_EXPIRATION_HOURS`)
- **Refresh Token:** Expira en 7 días
- **Rotación:** Los refresh tokens se rotan automáticamente

## 🛡️ Permisos

- **`AllowAny`**: Acceso público (registro, login, carrito y checkout para invitados)
- **`IsAuthenticatedOrReadOnly`**: Lectura pública, escritura requiere autenticación (productos, reseñas públicas, etc.)
- **`IsAuthenticated`**: Requiere usuario autenticado (perfil, historial de pedidos)
- **`IsAdmin`**: Requiere rol admin (panel y endpoints administrativos)

## 🔒 Seguridad

### Configuración de Producción

El backend está configurado con las mejores prácticas de seguridad:

- ✅ **HSTS** habilitado en producción
- ✅ **SSL Redirect** en producción
- ✅ **Cookies seguras** (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- ✅ **CORS** configurado correctamente
- ✅ **CSRF** protection habilitado
- ✅ **Rate limiting** en endpoints críticos
- ✅ **Validación de contraseñas** con validadores de Django
- ✅ **SSL/TLS** requerido para conexiones PostgreSQL (Supabase)

### CORS y CSRF

- **CORS** permite solicitudes desde `http://localhost:5173` y `http://127.0.0.1:5173` por defecto. Si ejecutas el frontend en otro puerto u origen (ej. `http://localhost:5174` o un dominio custom) agrégalo explícitamente en `CORS_ALLOWED_ORIGINS`.
- `CORS_EXPOSE_HEADERS` incluye `X-Session-Token` para que el frontend pueda leerlo y persistirlo. Si agregas más headers personalizados, expónlos aquí.
- `CSRF_TRUSTED_ORIGINS` refleja el mismo listado de orígenes.
- CSRF se mantiene activo para vistas basadas en formularios y el panel de administración. Las APIs REST que usan JWT en el header `Authorization` no requieren token CSRF adicional.

## 📊 Logging

El sistema de logging está configurado para registrar:

- **INFO**: Eventos generales de la aplicación
- **ERROR**: Errores de solicitudes HTTP
- **Archivo**: `backend/logs/django.log`

Los logs incluyen información sobre:
- Usuario que realiza la acción
- IP de la solicitud
- Endpoint accedido
- Errores y excepciones

**Logs de Webpay:** Todos los logs relacionados con Webpay tienen el prefijo `[WEBPAY]` para fácil identificación:
```
INFO [WEBPAY] Verificando buy_orders duplicados antes de crear...
INFO [WEBPAY] buy_order único generado: 'ORD-1-251118234635443'
INFO [WEBPAY] transaction.create() ejecutado sin excepciones
```

## 🗄️ Base de Datos

### Modelos Principales

#### Usuarios (`apps.users`)
- **`User`**: Modelo de usuario personalizado (extiende `AbstractUser`), email como `USERNAME_FIELD`, roles (cliente/admin)
- **`Address`**: Direcciones de envío de usuarios
- **`PasswordResetToken`**: Tokens para recuperación de contraseña

#### Productos (`apps.products`)
- **`Category`**: Categorías con jerarquía (`parent_category`, `level`, `sort_order`), imágenes
- **`Product`**: Productos con precios (enteros CLP), descuentos, stock, peso, imágenes, slug único
- **`ProductImage`**: Imágenes de productos con ordenamiento (`position`)
- **`ProductPriceHistory`**: Historial automático de cambios de precio (registrado vía signals)
- **`InventoryMovement`**: Movimientos de inventario (reservas, liberaciones, ventas)

#### Carrito (`apps.cart`)
- **`Cart`**: Carritos de compra (usuarios autenticados o invitados con `session_token`)
- **`CartItem`**: Items del carrito con producto, cantidad y precio fijado

#### Pedidos (`apps.orders`)
- **`OrderStatus`**: Estados de pedido (PENDING, PAID, FAILED, CANCELLED, PREPARING, SHIPPED, DELIVERED)
- **`Order`**: Pedidos con usuario (puede ser NULL para invitados), estado, monto total, costo de envío
- **`OrderItem`**: Items del pedido con snapshot de producto
- **`OrderItemSnapshot`**: Snapshot de datos de producto al momento de crear pedido
- **`OrderShippingSnapshot`**: Snapshot de datos de envío al momento de crear pedido
- **`PaymentTransaction`**: Transacciones de pago Webpay (token, buy_order, gateway_response, estado)
- **`PaymentStatus`**: Estados de pago (pending, approved, rejected, cancelled)
- **`ShippingZone`**: Zonas de envío (regiones)
- **`ShippingCarrier`**: Transportistas
- **`ShippingRule`**: Reglas de envío (por producto, categoría o general) con prioridad

#### Utilidades (`apps.common`)
- **`StoreConfig`**: Configuración global del sistema (parámetros configurables sin código)
- **`Currency`**: Utilidades de formato de moneda
- **`HeroCarousel`**: Carrusel principal de la página de inicio

#### Auditoría (`apps.audit`)
- **`AuditLog`**: Registro automático de acciones mediante middleware

### Estados de Pedido

Los estados disponibles son:
- `PENDING`: Pendiente de pago
- `PAID`: Pago confirmado
- `FAILED`: Pago fallido
- `CANCELLED`: Cancelado
- `PREPARING`: En preparación
- `SHIPPED`: Enviado
- `DELIVERED`: Entregado

### Transacciones Atómicas

El checkout utiliza transacciones atómicas con `SELECT FOR UPDATE` para:
- Bloquear filas de productos durante la validación
- Prevenir condiciones de carrera
- Garantizar que el stock se actualiza correctamente
- Revertir cambios si hay error

### Migraciones Importantes

- **0008_refactor_payment_transactions_webpay**: Refactor completo de PaymentTransaction con campos Webpay específicos
- **0010_add_performance_indexes**: Optimización de índices en productos, carrito y pedidos
- **0013_add_unique_constraint_webpay_buy_order**: Agrega constraint único en `webpay_buy_order` para prevenir duplicados (Error 21 de Transbank). **CRÍTICA** - Debe aplicarse antes de usar Webpay en producción.
- **Migración monetaria (0004)**: Conversión de DecimalField a PositiveIntegerField (CLP enteros)
- **Migración PostgreSQL**: Cambio de MySQL a PostgreSQL con configuración SSL para Supabase

## 🚀 Despliegue

### Verificación Pre-Despliegue

```bash
python manage.py check --deploy
```

Este comando verificará que todas las configuraciones de seguridad estén correctas.

### Ejecución de Tests Automatizados

```bash
python -m venv .venv
.venv\Scripts\activate  # En Windows PowerShell
pip install -r requirements.txt
pytest
```

> **Importante:** las pruebas utilizan una base de datos temporal. El costo de correrlas es bajo y cubren flujos críticos de autenticación y checkout.

### Auditoría de dependencias

```powershell
$env:PIPAPI_PYTHON_LOCATION = (Resolve-Path .\.venv\Scripts\python.exe)
pip-audit
```

> Ejecuta la auditoría desde el entorno virtual para asegurar que solo se analicen las dependencias del proyecto.

### Configuración para Producción

1. **Establecer `DEBUG=False`** en `.env`
2. **Configurar `ALLOWED_HOSTS`** con el dominio real
3. **Configurar `CORS_ALLOWED_ORIGINS`** con la URL del frontend
4. **Configurar `CSRF_TRUSTED_ORIGINS`** con la URL del frontend
5. **Configurar HTTPS** en el servidor web (Nginx/Apache)
6. **Usar un backend de email** real (no `console.EmailBackend`)
7. **Configurar variables de Webpay** con credenciales de producción
8. **Asegurar que `WEBPAY_RETURN_URL` y `WEBPAY_FINAL_URL`** sean URLs públicas (no localhost)

### Variables de Entorno en Producción

```env
DEBUG=False
SECRET_KEY=<clave-secreta-larga-y-aleatoria>
ALLOWED_HOSTS=condorshop.com,www.condorshop.com
CORS_ALLOWED_ORIGINS=https://condorshop.com,https://www.condorshop.com
CSRF_TRUSTED_ORIGINS=https://condorshop.com,https://www.condorshop.com
SECURE_SSL_REDIRECT=True

# PostgreSQL/Supabase
DB_NAME=condorshop
DB_USER=<usuario>
DB_PASSWORD=<contraseña>
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432

# Webpay Producción
WEBPAY_ENVIRONMENT=production
WEBPAY_COMMERCE_CODE=<tu-codigo-comercio>
WEBPAY_API_KEY=<tu-api-key>
WEBPAY_RETURN_URL=https://api.condorshop.com/api/payments/return/
WEBPAY_FINAL_URL=https://condorshop.com/payment/result
```

## 📝 Notas Importantes

### Funcionalidades Core
- ✅ El stock se descontará **transaccionalmente** al crear pedidos (con `select_for_update()`)
- ✅ Las imágenes se almacenan en `media/products/` y `media/categorias/`
- ✅ La auditoría registra acciones importantes en `audit_logs` (middleware automático)
- ✅ El sistema soporta **carritos de invitados** (sin autenticación, con `X-Session-Token`)
- ✅ Los precios se fijan al momento de agregar al carrito (no cambian después)
- ✅ El envío es **gratis** para compras sobre $50,000 CLP (configurable en `StoreConfig`)
- ✅ Los snapshots de pedidos capturan datos al momento de creación (precios, direcciones)
- ✅ El historial de precios se registra automáticamente al cambiar precios (signals)

### Webpay Plus
- ✅ **Webpay Plus está completamente funcional** - No es un placeholder
- ✅ **localhost funciona con Webpay** - No requiere tunneling en desarrollo
- ✅ Constraint único en `webpay_buy_order` previene Error 21 de Transbank
- ✅ Verificación proactiva de duplicados antes de crear transacción
- ✅ Manejo seguro de JSONField en PostgreSQL (raw SQL con `::jsonb`)

### Base de Datos
- ✅ PostgreSQL con soporte para Supabase (SSL requerido)
- ✅ Connection pooling configurado (CONN_MAX_AGE=600)
- ✅ Índices optimizados para queries frecuentes
- ✅ Transacciones atómicas con `ATOMIC_REQUESTS=True`

### Moneda
- ✅ **Todos los montos se manejan como enteros en CLP** (sin decimales)
- ✅ Formateo de precios es responsabilidad del frontend
- ✅ Cálculos de descuentos con redondeo half-up

### Rate limiting activo

- `POST /api/auth/register`: 5 solicitudes por minuto (clave `ip`)
- `POST /api/auth/login`: 5 solicitudes por minuto (clave `ip`)
- `POST /api/auth/password-reset` y endpoints relacionados: 3 solicitudes por hora (clave `ip`)
- `POST /api/checkout/shipping-quote`: 20 solicitudes por minuto (clave `ip`)
- `POST /api/orders/create`: 10 solicitudes por hora (clave `user`)

Estos límites mitigan fuerza bruta y abuso; ajusta las reglas `@ratelimit` si cambian los requisitos.

### Comportamiento especial en desarrollo (`DEBUG=True`)

- La raíz (`/`) redirige automáticamente a la pantalla de login del admin (`/admin/login/?next=/admin/`).
- Al iniciar `runserver`, todas las sesiones de Django se invalidan para forzar reautenticación.
- Las cookies de sesión expiran al cerrar el navegador o después de 30 minutos de inactividad.
- En producción (`DEBUG=False`) se mantiene el comportamiento habitual del sitio público.

### Healthcheck

- **Endpoint:** `GET /health/`
- **Checks:** realiza un `connection.ensure_connection()` contra la base de datos y retorna:
  ```json
  {
    "status": "ok",
    "checks": { "database": "ok" },
    "timestamp": "2025-11-08T12:34:56.789123"
  }
  ```
- Si la base de datos está inaccesible, responde con `503` y `"status": "unhealthy"`. Útil para probes de Kubernetes, load balancers o monitorización externa.

## 🔧 Integración Webpay Plus - Detalles Técnicos

### Servicio WebpayService

El servicio `apps.orders.services.WebpayService` encapsula toda la lógica de Webpay:

- **`create_transaction(order)`**: Crea una transacción en Webpay y retorna token y URL
- **`confirm_transaction(token)`**: Confirma una transacción después del callback

### Generación de buy_order

El `buy_order` se genera con el siguiente formato:
- Formato: `ORD-{order_id}-{YYMMDDHHMMSS}{microsegundos_3digitos}`
- Ejemplo: `ORD-1-251118234635443` (21 caracteres)
- Límite: 26 caracteres máximo (validación de Transbank SDK)
- Unicidad: Verificación proactiva en BD antes de crear + constraint único

### Manejo de gateway_response

El campo `gateway_response` (JSONField) se maneja con raw SQL para evitar errores de deserialización cuando PostgreSQL devuelve JSONB como dict de Python.

### Logs y Debugging

Todos los logs de Webpay tienen prefijo `[WEBPAY]`:
```
INFO [WEBPAY] Verificando buy_orders duplicados antes de crear...
INFO [WEBPAY] buy_order único generado: 'ORD-1-251118234635443'
INFO [WEBPAY] transaction.create() ejecutado sin excepciones
ERROR [WEBPAY] ERROR: Error al crear transacción: ...
```

### Correcciones Implementadas (Noviembre 2025)

1. **Límite de buy_order corregido:** De 64 a 26 caracteres (límite real de Transbank)
2. **Formato optimizado:** `ORD-{id}-{timestamp}` en lugar de `ORDER-{id}-{timestamp}` (21 caracteres)
3. **Microsegundos:** Incluidos para mayor unicidad
4. **Constraint único:** Migración 0013 previene duplicados a nivel de BD
5. **Verificación proactiva:** Chequea duplicados antes de crear transacción
6. **Manejo seguro de JSONField:** Raw SQL para evitar errores de deserialización en PostgreSQL
7. **Migración MySQL → PostgreSQL:** Configuración SSL, psycopg2-binary, django.contrib.postgres
8. **Optimización de índices:** Índices en campos críticos para mejorar performance
9. **Migración monetaria:** Conversión a CLP enteros para evitar problemas de precisión

## 🔧 Comandos de Gestión Disponibles

### Comandos Django
- `python manage.py load_initial_data` - Cargar datos de ejemplo (categorías, productos, usuarios)
- `python manage.py analyze_indexes` - Analizar uso de índices en queries críticas
- `python manage.py release_expired_reservations` - Liberar reservas de stock expiradas
- `python manage.py clean_payment_transactions` - Limpiar transacciones antiguas

### Testing
- `pytest` - Ejecutar todos los tests
- `pytest -v` - Ejecutar tests con output verbose
- `pytest --cov` - Ejecutar tests con cobertura de código
