# CondorShop - Frontend

Frontend SPA para CondorShop construido con React 18.3.1, Vite 7.2.1, React Router v6, Tailwind CSS 3.4.13, Axios 1.13.2, Zustand 4.5.5 y React Hook Form 7.66.0. Integración completa con Webpay Plus para procesamiento de pagos.

**Última actualización:** Noviembre 2025

## 🔒 Estado de Seguridad

✅ **Todas las vulnerabilidades resueltas** (última auditoría: Noviembre 2025)
- Vite 7.2.1 (última versión estable)
- Axios 1.13.2 (sin vulnerabilidades conocidas)
- React Hook Form 7.66.0 (actualizado)
- React 18.3.1 (LTS)
- Auditoría `npm audit --omit=dev` sin hallazgos críticos

## Requisitos

- **Node.js**: 18+ (recomendado: 20+ LTS)
- **npm**: 9+ (viene con Node.js)

## 🛠️ Stack Tecnológico

### Core
- **React**: 18.3.1
- **Vite**: 7.2.1 (Build tool y dev server)
- **React Router DOM**: 6.26.0

### Estado y Formularios
- **Zustand**: 4.5.5 (Estado global)
- **React Hook Form**: 7.66.0 (Validación de formularios)

### Estilos
- **Tailwind CSS**: 3.4.13
- **PostCSS**: 8.4.47
- **Autoprefixer**: 10.4.20

### HTTP y Utilidades
- **Axios**: 1.13.2 (Cliente HTTP)
- **ESLint**: 8.57.0 (Linting)

## Instalación

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
Crear archivo `.env` en la raíz de `frontend/` con:
```env
VITE_API_URL=http://localhost:8000/api
VITE_WEBPAY_ENABLED=true
```

3. Ejecutar servidor de desarrollo:
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

## Estructura del Proyecto

```
frontend/
├── public/              # Archivos estáticos
├── src/
│   ├── assets/         # Imágenes y recursos
│   ├── components/     # Componentes reutilizables
│   │   ├── checkout/   # CheckoutStepper
│   │   ├── common/     # Header, Footer, Button, Modal, Spinner, Toast, ErrorBoundary, OptimizedImage
│   │   ├── forms/      # TextField, Select, QuantityStepper
│   │   ├── home/       # HeroCarousel, CategoryGrid, ProductRail
│   │   ├── products/   # ProductCard, ProductGallery, PriceTag
│   │   └── profile/    # AddressForm
│   ├── constants/      # Constantes (regions.js)
│   ├── pages/          # Páginas de la aplicación
│   │   ├── Auth/       # Login, Register, ForgotPassword, ResetPassword
│   │   ├── Checkout/   # StepCustomer, StepAddress, StepPayment, StepReview
│   │   ├── Admin/      # Páginas de administración (si aplica)
│   │   └── [Otras]     # Home, Cart, ProductDetail, CategoryPage, Profile, Orders, PaymentResultPage
│   ├── routes/         # Configuración de rutas (AppRoutes, ProtectedRoute)
│   ├── services/       # Servicios API (Axios): auth, products, cart, orders, categories, payments, users
│   ├── store/          # Zustand stores (authSlice, cartSlice, checkoutSlice)
│   ├── utils/          # Utilidades (authToken, formatPrice, getProductImage, storage, validations)
│   ├── App.jsx         # Componente principal
│   └── main.jsx        # Punto de entrada
└── package.json
```

## ✨ Funcionalidades Principales

### Catálogo y Búsqueda
- ✅ Listado de productos con paginación (20 por página)
- ✅ Búsqueda en tiempo real (requiere botón "Buscar")
- ✅ Filtros por categoría y rango de precios
- ✅ Ordenamiento por precio (ascendente/descendente)
- ✅ Productos destacados (Ofertas, Populares)
- ✅ Galería de imágenes por producto

### Carrito de Compras
- ✅ Agregar/eliminar productos
- ✅ Actualizar cantidades con validación de stock
- ✅ Cálculo automático de subtotal, envío y total
- ✅ Envío gratis automático (umbral: $50,000 CLP)
- ✅ Sincronización con backend mediante `X-Session-Token`

### Checkout Multipaso
- ✅ **Usuario autenticado:** Address → Payment → Review
- ✅ **Invitado:** Customer → Address → Payment → Review
- ✅ Cotización de envío en tiempo real
- ✅ Resumen de productos antes de pagar
- ✅ Validación de formularios con React Hook Form

### Autenticación
- ✅ Registro de nuevos usuarios
- ✅ Login con JWT (access + refresh tokens)
- ✅ Recuperación de contraseña (✅ Funcional)
- ✅ Verificación de token antes de reset
- ✅ Perfil editable con gestión de direcciones

### Pedidos
- ✅ Historial de pedidos del usuario
- ✅ Detalle completo de pedido con estados
- ✅ Reintentar pago para pedidos fallidos
- ✅ Cancelar pedidos pendientes
- ✅ Línea de tiempo de estados

### Pagos Webpay Plus
- ✅ Iniciar pago Webpay desde checkout
- ✅ Redirección automática a Webpay
- ✅ Página de resultado con información completa
- ✅ Consulta de estado de pago

## Características

### Páginas Públicas

- **Home**: Catálogo con búsqueda, filtros por precio, ordenamiento y paginación. Incluye HeroCarousel, CategoryGrid y ProductRail
- **ProductDetail**: Detalle de producto con galería de imágenes (ProductGallery), descripción completa, precios formateados
- **CategoryPage**: Página de categoría con productos filtrados, búsqueda y ordenamiento
- **Cart**: Carrito de compras con edición de cantidades, cálculo de envío y totales
- **Login/Register**: Autenticación de usuarios con validación de formularios
- **ForgotPassword/ResetPassword**: Recuperación de contraseña con token de validación (✅ Funcional)
- **PaymentResultPage**: Página de resultado de pago Webpay con información completa de transacción (✅ Funcional)

### Checkout Multipaso

**Usuario Logueado:**
1. **Carrito**: Resumen y productos
2. **StepAddress**: Selección/creación de dirección y método de entrega
3. **StepPayment**: Método de pago (Webpay Plus - ✅ Funcional)
4. **StepReview**: Revisión y confirmación de pedido

**Invitado:**
1. **Carrito**: Resumen y productos
2. **StepCustomer**: Datos del cliente (mínimos requeridos)
3. **StepAddress**: Dirección y método de entrega
4. **StepPayment**: Método de pago (Webpay Plus - ✅ Funcional)
5. **StepReview**: Revisión y confirmación de pedido

Durante este flujo el frontend solicita cotizaciones de envío en tiempo real mediante `/api/checkout/shipping-quote` y reutiliza el `X-Session-Token` entregado por el backend para mantener sincronizado el carrito del invitado.

### Páginas Protegidas (Cliente)

- **Profile**: Perfil y datos personales, gestión de direcciones
- **Orders**: Historial de pedidos con estados, detalles y acciones (reintentar pago, cancelar)

### Integración Webpay Plus

**✅ COMPLETAMENTE FUNCIONAL**

El frontend incluye integración completa con Webpay Plus:

1. **Iniciar pago:** `paymentsService.initiateWebpayPayment(orderId)`
2. **Redirigir a Webpay:** `paymentsService.redirectToWebpay(token, url)` - Crea formulario POST automático
3. **Verificar estado:** `paymentsService.getPaymentStatus(orderId)` - Consulta estado después del callback
4. **Página de resultado:** `PaymentResultPage` muestra información completa según requerimientos de Transbank

**Flujo completo:**
1. Usuario completa checkout y crea orden
2. Frontend llama a `/api/orders/{id}/pay/`
3. Backend retorna `{ token, url, buy_order }`
4. Frontend redirige automáticamente a Webpay con formulario POST
5. Usuario paga en Webpay
6. Webpay redirige a `/payment/result?status=success&order_id=123`
7. Frontend consulta `/api/payments/status/{order_id}/` para obtener detalles
8. Muestra página de resultado con información completa

**Habilitar Webpay:**
```env
VITE_WEBPAY_ENABLED=true
```

**⚠️ IMPORTANTE:** Webpay funciona correctamente con `localhost` en desarrollo. No requiere tunneling.

## Estado Global (Zustand)

### authSlice
- Maneja autenticación, token, usuario y rol
- Persiste token en localStorage
- Métodos: `login`, `logout`, `setUser`, `setToken`

### cartSlice
- Maneja carrito, subtotal, envío y total
- Calcula envío gratis automáticamente (umbral: $50,000 CLP)
- Sincroniza con backend mediante `X-Session-Token`
- Métodos: `addItem`, `removeItem`, `updateQuantity`, `clearCart`, `setCart`

### checkoutSlice
- Maneja estado del checkout
- Campos: `paymentMethod`, `canPay`, `deliveryMethod`, `couponCode`
- Persiste datos temporales en sessionStorage (invitados)
- Métodos: `setPaymentMethod`, `setDeliveryMethod`, `setCanPay`

## Integración API

El frontend consume la API del backend usando:
- Base URL: `VITE_API_URL` (default: http://localhost:8000/api)
- Autenticación JWT mediante header `Authorization: Bearer <token>`
- Interceptor Axios para manejo automático de tokens y errores 401
- Header `X-Session-Token` para carritos de invitados

### Servicios API Implementados

#### auth.js
- `register(email, password, ...)` - Registro de usuario
- `login(email, password)` - Login y obtención de tokens
- `logout()` - Cerrar sesión
- `getProfile()` - Obtener perfil
- `updateProfile(data)` - Actualizar perfil

#### products.js
- `getProducts(params)` - Listar productos con filtros
- `getProduct(slug)` - Obtener detalle de producto
- `getCategories()` - Listar categorías

#### cart.js
- `getCart()` - Obtener carrito actual
- `addToCart(productId, quantity)` - Agregar producto
- `updateCartItem(itemId, quantity)` - Actualizar cantidad
- `removeCartItem(itemId)` - Eliminar item

#### orders.js
- `getOrders()` - Historial de pedidos
- `getOrder(orderId)` - Detalle de pedido
- `createOrder(data)` - Crear pedido desde carrito
- `cancelOrder(orderId)` - Cancelar pedido

#### paymentsService.js
- `initiateWebpayPayment(orderId)` - Iniciar pago Webpay
- `getPaymentStatus(orderId)` - Consultar estado de pago
- `redirectToWebpay(token, url)` - Redirigir a Webpay

#### users.js
- `getAddresses()` - Listar direcciones
- `createAddress(data)` - Crear dirección
- `updateAddress(id, data)` - Actualizar dirección
- `deleteAddress(id)` - Eliminar dirección

#### categories.js
- `getCategories()` - Listar categorías

### Endpoints Utilizados

- **Auth**: `/api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/auth/verify-reset-token/{token}/`, `/api/users/profile`
- **Productos**: `/api/products/`, `/api/products/{slug}/`, `/api/products/categories/`
- **Carrito**: `/api/cart/`, `/api/cart/add`, `/api/cart/items/{id}`, `/api/cart/items/{id}/delete`
- **Checkout**: `/api/checkout/mode`, `/api/checkout/shipping-quote`, `/api/checkout/create`
- **Pedidos**: `/api/orders/`, `/api/orders/{id}/`, `/api/orders/{id}/pay/`, `/api/orders/{id}/cancel/`
- **Pagos**: `/api/payments/return/`, `/api/payments/status/{order_id}/`
- **Usuarios**: `/api/users/addresses`, `/api/users/addresses/{id}`

Ver `backend/README.md` para documentación completa de la API.

## Routing

### Rutas Públicas
- `/` - Home
- `/category/:slug` - Página de categoría
- `/product/:slug` - Detalle de producto
- `/cart` - Carrito
- `/login` - Login
- `/register` - Registro
- `/forgot-password` - Solicitar reset de contraseña
- `/reset-password` - Restablecer contraseña
- `/checkout/customer` - Datos de cliente (invitados)
- `/checkout/address` - Dirección de envío
- `/checkout/payment` - Método de pago
- `/checkout/review` - Revisión final
- `/payment/result` - Resultado de pago Webpay

### Rutas Protegidas (Cliente)
- `/profile` - Perfil de usuario
- `/orders` - Historial de pedidos

### Rutas Protegidas (Admin)
- `/admin/*` - Panel de administración (si aplica)

## Scripts Disponibles

- `npm run dev`: Servidor de desarrollo (http://localhost:5173)
- `npm run build`: Build de producción (genera `dist/`)
- `npm run preview`: Preview del build de producción
- `npm run lint`: Ejecutar linter (ESLint)

## Versiones Soportadas

### Herramientas Principales
- **Vite**: 7.2.1+
- **React**: 18.3.1+
- **React Router**: 6.26.0+
- **Tailwind CSS**: 3.4.13+
- **Zustand**: 4.5.5+
- **React Hook Form**: 7.66.0+
- **Axios**: 1.13.2+

### Verificación de Seguridad
```bash
npm audit --omit=dev   # Auditar vulnerabilidades de runtime
npm audit fix          # Corregir automáticamente (si es seguro)
```

## Variables de Entorno

Crear archivo `.env` en la raíz de `frontend/` con:

```env
VITE_API_URL=http://localhost:8000/api
VITE_WEBPAY_ENABLED=true
```

### Variables Explicadas

- **VITE_API_URL**: URL base de la API del backend (requerido)
  - Desarrollo: `http://localhost:8000/api`
  - Producción: `https://api.condorshop.com/api`

- **VITE_WEBPAY_ENABLED**: Habilitar integración Webpay (default: `false`)
  - `true`: Webpay completamente funcional
  - `false`: Webpay deshabilitado (modo placeholder)

**⚠️ IMPORTANTE:** Todas las variables de entorno deben comenzar con `VITE_` para que Vite las exponga al código.

## Componentes Principales

### Common
- **Header**: Navegación principal con carrito y usuario
- **Footer**: Pie de página
- **Button**: Botón reutilizable con variantes
- **Modal**: Modal genérico
- **Spinner**: Indicador de carga
- **Toast**: Notificaciones toast
- **ErrorBoundary**: Manejo de errores React
- **OptimizedImage**: Componente de imagen optimizada

### Forms
- **TextField**: Input de texto con validación
- **Select**: Select con opciones
- **QuantityStepper**: Selector de cantidad (+/-)

### Products
- **ProductCard**: Tarjeta de producto para listados
- **ProductGallery**: Galería de imágenes de producto
- **PriceTag**: Etiqueta de precio con descuentos

### Checkout
- **CheckoutStepper**: Indicador de pasos del checkout

### Home
- **HeroCarousel**: Carrusel principal
- **CategoryGrid**: Grid de categorías
- **ProductRail**: Rail de productos destacados

### Profile
- **AddressForm**: Formulario de dirección

## Notas Importantes

### Carrito y Sesiones
- El carrito se sincroniza con el backend mediante `X-Session-Token`; el token se almacena en `localStorage` y se adjunta automáticamente en cada petición mediante interceptor Axios.
- Los datos temporales del paso `StepCustomer` para invitados se guardan en `sessionStorage`.
- Si un invitado se autentica, el carrito se fusiona automáticamente con el usuario.

### Precios y Envíos
- **Todos los montos se reciben como enteros en CLP** (sin decimales)
- El formateo de precios (`$19.990`) es responsabilidad del frontend (utilidad `formatPrice`)
- Envío gratis aplica cuando el subtotal >= CLP 50.000 (configurable en backend `StoreConfig`)

### Autenticación y Permisos
- Las rutas admin requieren rol `admin` (verificado en `ProtectedRoute`)
- Los formularios usan React Hook Form para validación client-side
- Tokens JWT se almacenan en `localStorage` (considerar httpOnly cookies en producción)

### Webpay Plus
- **Webpay Plus está completamente funcional** - No es un placeholder
- **Reset password está completamente funcional** - Backend y frontend implementados
- **localhost funciona con Webpay** - No requiere tunneling en desarrollo
- La redirección a Webpay se hace mediante formulario POST automático
- La página de resultado muestra información completa según requerimientos de Transbank

### Optimizaciones
- Lazy loading de imágenes con componente `OptimizedImage`
- Estado global con Zustand para evitar prop drilling
- Interceptor Axios para manejo automático de tokens y errores

### Estados de pedido en la UI

La página `Orders` muestra los estados entregados por el backend (`PENDING`, `PAID`, `FAILED`, `CANCELLED`, `PREPARING`, `SHIPPED`, `DELIVERED`) usando badges con colores consistentes:
- `PENDING` / `PREPARING`: amarillo
- `PAID` / `SHIPPED`: azul
- `DELIVERED`: verde
- `FAILED` / `CANCELLED`: rojo

Además se renderiza la línea de tiempo del pedido a partir de `status_history` y se formatean fechas/monedas con los helpers de `utils/formatPrice` y `utils/dates`.

### Página de Resultado de Pago

`PaymentResultPage` muestra información completa según requerimientos de Transbank:
- Número de orden
- Nombre del comercio
- Monto pagado y moneda
- Fecha de transacción
- Código de autorización
- Tipo de pago (Débito/Crédito)
- Cantidad de cuotas
- Últimos 4 dígitos de tarjeta
- Lista de productos adquiridos

## Seguridad

### ✅ Medidas Implementadas
- Dependencias actualizadas a versiones seguras
- Variables de entorno para configuración (no hardcodeadas)
- Interceptor Axios para manejo seguro de tokens
- Validación de autenticación en rutas protegidas
- Headers CORS/CSRF configurados correctamente
- Tokens JWT almacenados en localStorage (considerar httpOnly cookies en producción)

### 📋 Auditoría de Seguridad
- Ejecutar `npm audit` regularmente
- Verificar dependencias actualizadas
- Revisar vulnerabilidades conocidas

## Troubleshooting

### Problemas Comunes

**Error: "Cannot find module 'vite'"**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Puerto 5173 ya en uso**
- Cambiar puerto en `vite.config.js` o matar el proceso que lo usa

**Error de CORS**
- Verificar que `VITE_API_URL` apunta al backend correcto
- Verificar que backend tiene `CORS_ALLOWED_ORIGINS` con `http://localhost:5173`

**Webpay no redirige**
- Verificar que `VITE_WEBPAY_ENABLED=true` en `.env`
- Verificar que backend tiene Webpay configurado correctamente
- Revisar consola del navegador para errores

**Token JWT expirado**
- El interceptor Axios debería manejar esto automáticamente
- Si persiste, verificar que el refresh token es válido

**Carrito no se sincroniza (invitado)**
- Verificar que `X-Session-Token` se envía en headers
- Verificar que el token se guarda en localStorage después de primera petición
- Revisar Network tab en DevTools para ver headers

## Integración con Backend

### Autenticación JWT

1. Usuario hace login → Backend retorna `{ access, refresh }`
2. Frontend guarda tokens en `authSlice` (Zustand)
3. Interceptor Axios agrega `Authorization: Bearer <access>` a todas las peticiones
4. Si token expira (401), interceptor intenta refresh automáticamente
5. Si refresh falla, redirige a `/login`

### Manejo de X-Session-Token (Invitados)

1. Primera petición sin autenticación → Backend genera `X-Session-Token`
2. Frontend lee header `X-Session-Token` de respuesta
3. Guarda token en localStorage
4. Interceptor Axios agrega `X-Session-Token` a todas las peticiones subsecuentes
5. Si usuario se autentica, carrito se fusiona automáticamente

### Manejo de Errores

- Errores 400/404: Se muestran como toast notifications
- Errores 401: Interceptor maneja refresh automático
- Errores 403: Redirige a página de acceso denegado
- Errores 500: Muestra mensaje genérico de error del servidor

## Build de Producción

```bash
npm run build
```

Esto genera una carpeta `dist/` con los archivos optimizados listos para desplegar.

**Configuración recomendada:**
- Servir archivos estáticos con un servidor web (Nginx, Apache)
- Configurar HTTPS (requerido para producción)
- Configurar variables de entorno de producción:
  ```env
  VITE_API_URL=https://api.condorshop.com/api
  VITE_WEBPAY_ENABLED=true
  ```
- Habilitar compresión gzip/brotli
- Configurar caché para assets estáticos (long-term caching)
- Configurar CSP (Content Security Policy) headers
- Considerar CDN para assets estáticos

## 📚 Documentación Adicional

- **Backend API:** Ver `../backend/README.md` para documentación completa de endpoints
- **Contrato de Integración:** Ver `../backend/docs/INTEGRATION_CONTRACT.md` para especificaciones detalladas
- **Webpay:** Ver `../backend/docs/WEBPAY_HISTORICO.md` para detalles técnicos de la integración
