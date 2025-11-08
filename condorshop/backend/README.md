# CondorShop - Backend API

Backend Django 5.x con Django REST Framework para plataforma e-commerce académica.

## ⚡ Inicio Rápido

### Comando Simplificado

Desde el directorio raíz del proyecto:

```powershell
cd backend
python manage.py runserver
```

**¡Eso es todo!** El script `manage.py` automáticamente detectará y usará el entorno virtual local.

## 📋 Requisitos

- Python 3.11+
- MySQL 8.0
- pip

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

# Editar .env con tus credenciales de base de datos
```

4. **Crear la base de datos MySQL:**
```sql
CREATE DATABASE condorshop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

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
- `DB_NAME`: Nombre de la base de datos (default: `condorshop`)
- `DB_USER`: Usuario de MySQL
- `DB_PASSWORD`: Contraseña de MySQL
- `DB_HOST`: Host de MySQL (default: `localhost`)
- `DB_PORT`: Puerto de MySQL (default: `3306`)

### Opcionales
- `ALLOWED_HOSTS`: Lista de hosts permitidos (default: `localhost,127.0.0.1`)
- `CORS_ALLOWED_ORIGINS`: URLs del frontend separadas por comas (default: `http://localhost:5173,http://127.0.0.1:5173`)
- `CSRF_TRUSTED_ORIGINS`: URLs confiables para CSRF (default: igual que CORS)
- `JWT_EXPIRATION_HOURS`: Horas de expiración del token JWT (default: `24`)
- `EMAIL_BACKEND`: Backend de email (default: `django.core.mail.backends.console.EmailBackend`)

### Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**⚠️ IMPORTANTE:** Nunca compartas tu `SECRET_KEY` ni la subas a control de versiones.

## Estructura del Proyecto

```
backend/
├── condorshop_api/     # Configuración del proyecto
├── apps/
│   ├── users/          # Usuarios y autenticación
│   ├── products/       # Catálogo de productos
│   ├── cart/           # Carrito de compras
│   ├── orders/         # Pedidos y estados
│   ├── admin_panel/    # Panel de administración
│   └── audit/          # Auditoría
└── media/              # Archivos multimedia
```

### Productos / Descuentos

**Descuentos:**
- `discount_percent`: entero 1-100
- `discount_amount` y `discount_price`: enteros (CLP)
- Precedencia de cálculo: `final_price` > `amount` > `percent`
- Todos los precios se manejan como enteros en pesos (sin decimales)
- El campo `price` se almacena como `DecimalField` con dos decimales y DRF lo expone como string (ej: `"45990.00"`). Los campos calculados `final_price`, `discount_price`, `discount_amount` y `calculated_discount_percent` se devuelven como enteros en CLP para facilitar el formateo en frontend.

## 📡 Endpoints de la API

### Autenticación (`/api/auth/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/api/auth/register` | Registro de nuevo cliente | `AllowAny` |
| POST | `/api/auth/login` | Login de usuario (retorna JWT) | `AllowAny` |
| POST | `/api/auth/token/` | Obtener token JWT (SimpleJWT) | `AllowAny` |
| POST | `/api/auth/token/refresh/` | Refrescar token JWT | `AllowAny` |
| GET/PATCH | `/api/users/profile` | Ver/editar perfil de usuario | `IsAuthenticated` |

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

#### Endpoints pendientes

- `/api/auth/forgot-password` *(pendiente)*  
- `/api/auth/reset-password` *(pendiente)*  

> El frontend expone las pantallas correspondientes pero el backend aún no implementa los endpoints. Se mantienen en backlog para una futura iteración.

### Productos (`/api/products/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/products/` | Listado con paginación, búsqueda, filtros | `IsAuthenticatedOrReadOnly` |
| GET | `/api/products/{slug}/` | Detalle de producto | `IsAuthenticatedOrReadOnly` |
| GET | `/api/products/categories/` | Listado de categorías | `IsAuthenticatedOrReadOnly` |

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
| PATCH | `/api/cart/items/{id}/` | Actualizar cantidad de item | `AllowAny` |
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

### Panel de Administración (`/api/admin/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET/POST | `/api/admin/products` | CRUD de productos | `IsAuthenticated` + `IsAdmin` |
| GET/PATCH/DELETE | `/api/admin/products/{id}` | Operaciones sobre producto | `IsAuthenticated` + `IsAdmin` |
| POST | `/api/admin/products/{id}/images` | Subir imagen a producto (form-data: `image`, `alt_text` opcional, `position` opcional) | `IsAuthenticated` + `IsAdmin` |
| GET | `/api/admin/orders` | Lista de todos los pedidos (filtros: `status`, `customer_email`, `date_from`, `date_to`) | `IsAuthenticated` + `IsAdmin` |
| GET | `/api/admin/orders/{id}` | Detalle de un pedido | `IsAuthenticated` + `IsAdmin` |
| PATCH | `/api/admin/orders/{id}/status` | Cambiar estado de pedido (Body: `{ "status_id": 2, "note": "..." }`) | `IsAuthenticated` + `IsAdmin` |
| GET | `/api/admin/orders/export` | Exportar pedidos a CSV (query params: `status`, `date_from`, `date_to`) | `IsAuthenticated` + `IsAdmin` |
| GET | `/api/admin/order-statuses` | Lista de estados de pedido | `IsAuthenticated` + `IsAdmin` |

## 📥 Formato de respuestas y errores

- **Éxito (2xx):** Los endpoints retornan payloads JSON consistentes con los serializers correspondientes.
- **Errores de validación (400):** Se devuelven como diccionario `{ "campo": ["mensaje"] }`.
- **Errores de negocio (400/404):** Se normalizan en `{ "error": "mensaje descriptivo" }`.
- **Autenticación (401) / Autorización (403):** `{ "detail": "Authentication credentials were not provided." }` conforme a DRF.
- **Rate limiting (429):** `{ "detail": "Request was throttled." }`.

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

- **`AllowAny`**: Acceso público (registro, login)
- **`IsAuthenticatedOrReadOnly`**: Lectura pública, escritura requiere autenticación (productos, carrito)
- **`IsAuthenticated`**: Requiere usuario autenticado (perfil, órdenes)
- **`IsAdmin`**: Requiere rol admin (panel de administración)

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

### CORS y CSRF

- **CORS** permite solicitudes desde `http://localhost:5173` y `http://127.0.0.1:5173` por defecto
- **CSRF_TRUSTED_ORIGINS** configurado para las mismas URLs
- En producción, actualizar `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` con las URLs reales

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

## 🗄️ Base de Datos

### Modelos Principales

- **users.User**: Modelo de usuario personalizado
- **products.Product**: Catálogo de productos
- **products.Category**: Categorías de productos
- **cart.Cart**: Carritos de compra
- **orders.Order**: Pedidos
- **orders.OrderStatus**: Estados de pedido
- **orders.Payment**: Pagos
- **audit.AuditLog**: Bitácora de auditoría

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

### Variables de Entorno en Producción

```env
DEBUG=False
SECRET_KEY=<clave-secreta-larga-y-aleatoria>
ALLOWED_HOSTS=condorshop.com,www.condorshop.com
CORS_ALLOWED_ORIGINS=https://condorshop.com,https://www.condorshop.com
CSRF_TRUSTED_ORIGINS=https://condorshop.com,https://www.condorshop.com
SECURE_SSL_REDIRECT=True
```

## 📝 Notas Importantes

- ✅ El stock se descontará **transaccionalmente** al crear pedidos
- ✅ Las imágenes se almacenan en `media/products/`
- ✅ La auditoría registra acciones importantes en `audit_logs`
- ✅ El sistema soporta **carritos de invitados** (sin autenticación)
- ✅ Los precios se fijan al momento de agregar al carrito
- ✅ El envío es **gratis** para compras sobre $50,000 CLP

