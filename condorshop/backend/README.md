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

### Carrito (`/api/cart/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/cart/` | Ver carrito actual | `IsAuthenticatedOrReadOnly` |
| POST | `/api/cart/add` | Agregar producto al carrito | `IsAuthenticatedOrReadOnly` |
| PATCH | `/api/cart/items/{id}/` | Actualizar cantidad de item | `IsAuthenticatedOrReadOnly` |
| DELETE | `/api/cart/items/{id}/delete` | Eliminar item del carrito | `IsAuthenticatedOrReadOnly` |

**Nota:** Los usuarios no autenticados pueden usar el carrito con un `X-Session-Token` en los headers.

### Pedidos (`/api/orders/` y `/api/checkout/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/checkout/mode` | Información del modo de checkout | `IsAuthenticatedOrReadOnly` |
| POST | `/api/checkout/create` | Crear pedido desde el carrito | `IsAuthenticatedOrReadOnly` |
| GET | `/api/orders/` | Historial de pedidos del usuario | `IsAuthenticated` |
| GET | `/api/orders/{id}/` | Detalle de un pedido | `IsAuthenticated` |

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

