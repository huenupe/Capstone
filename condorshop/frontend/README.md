# CondorShop - Frontend

Frontend SPA para CondorShop construido con React 18, Vite, React Router v6, Tailwind CSS, Axios, Zustand y React Hook Form.

## 🔒 Estado de Seguridad

✅ **Todas las vulnerabilidades resueltas** (última auditoría: 2025-01-27)
- Vite actualizado a 7.1.12 (vulnerabilidad esbuild corregida)
- Auditoría limpia: 0 vulnerabilidades detectadas
- Ver `SECURITY_REMEDIATION_PLAN.md` para detalles completos

## Requisitos

- **Node.js**: 18+ (recomendado: 20+ LTS)
- **npm**: 9+ (viene con Node.js)

## Instalación

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
Crear archivo `.env` en la raíz de `frontend/` con:
```
VITE_API_URL=http://localhost:8000/api
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
│   │   ├── common/     # Header, Footer, Button, Modal, Spinner, Toast
│   │   ├── forms/      # TextField, Select, QuantityStepper
│   │   ├── home/       # HeroCarousel, CategoryGrid, ProductRail
│   │   └── products/   # ProductCard, ProductGallery, PriceTag
│   ├── pages/          # Páginas de la aplicación
│   │   ├── Auth/       # Login, Register, ForgotPassword, ResetPassword
│   │   ├── Checkout/   # StepCustomer, StepAddress, StepPayment, StepReview
│   │   ├── Admin/      # Dashboard, Products, Orders
│   │   └── [Otras]     # Home, Cart, ProductDetail, CategoryPage, Profile, Orders
│   ├── routes/         # Configuración de rutas (AppRoutes, ProtectedRoute, RoleRoute)
│   ├── services/       # Servicios API (Axios): auth, products, cart, orders, admin, categories
│   ├── store/          # Zustand stores (authSlice, cartSlice, checkoutSlice)
│   ├── utils/          # Utilidades (authToken, formatPrice, getProductImage, storage, validations)
│   ├── App.jsx         # Componente principal
│   └── main.jsx        # Punto de entrada
└── package.json
```

## Características

### Páginas Públicas
- **Home**: Catálogo con búsqueda, filtros y paginación
- **ProductDetail**: Detalle de producto con galería
- **Cart**: Carrito de compras con edición de cantidades
- **Login/Register**: Autenticación de usuarios

### Checkout Multipaso

**Usuario Logueado:**
1. **Carrito**: Resumen y productos
2. **StepAddress**: Dirección y método de entrega
3. **StepPayment**: Método de pago (Webpay placeholder)
4. **StepReview**: Revisión y confirmación de pedido

**Invitado:**
1. **Carrito**: Resumen y productos
2. **StepCustomer**: Datos del cliente (mínimos)
3. **StepAddress**: Dirección y método de entrega
4. **StepPayment**: Método de pago (Webpay placeholder)
5. **StepReview**: Revisión y confirmación de pedido

### Páginas Protegidas (Cliente)
- **Profile**: Perfil y datos personales
- **Orders**: Historial de pedidos

### Panel Admin
- **Dashboard**: Estadísticas generales
- **Products**: CRUD de productos con subida de imágenes
- **Orders**: Gestión de pedidos con filtros y exportación CSV

## Estado Global (Zustand)

- **authSlice**: Maneja autenticación, token, usuario y rol
- **cartSlice**: Maneja carrito, subtotal, envío y total (con umbral de envío gratis)
- **checkoutSlice**: Maneja estado del checkout (paymentMethod, canPay, deliveryMethod, couponCode)

## Integración API

El frontend consume la API del backend usando:
- Base URL: `VITE_API_URL` (default: http://localhost:8000/api)
- Autenticación JWT mediante header `Authorization: Bearer <token>`
- Interceptor Axios para manejo automático de tokens y errores 401

### Endpoints Utilizados

- **Auth**: `/api/auth/register`, `/api/auth/login`, `/api/users/profile`
  - ⚠️ **Nota**: Existen páginas `ForgotPassword` y `ResetPassword` pero los endpoints del backend aún no están implementados
- **Productos**: `/api/products/`, `/api/products/{slug}/`, `/api/products/categories/`
- **Carrito**: `/api/cart/`, `/api/cart/add`, `/api/cart/items/{id}`, `/api/cart/items/{id}/delete`
- **Pedidos**: `/api/checkout/mode`, `/api/checkout/create`, `/api/orders/`, `/api/orders/{id}/`
- **Admin**: `/api/admin/products`, `/api/admin/orders`, `/api/admin/order-statuses`

Ver `backend/README.md` para documentación completa de la API.

## Scripts Disponibles

- `npm run dev`: Servidor de desarrollo (http://localhost:5173)
- `npm run build`: Build de producción (genera `dist/`)
- `npm run preview`: Preview del build de producción
- `npm run lint`: Ejecutar linter (ESLint)

## Versiones Soportadas

### Herramientas Principales
- **Vite**: 7.1.12+
- **React**: 18.3.1+
- **React Router**: 6.26.0+
- **Tailwind CSS**: 3.4.13+

### Verificación de Seguridad
```bash
npm audit          # Auditar vulnerabilidades
npm audit fix      # Corregir automáticamente (si es seguro)
```

## Variables de Entorno

Crear archivo `.env` en la raíz de `frontend/` con:

```env
VITE_API_URL=http://localhost:8000/api
VITE_PAYMENTS_PROVIDER=webpay
VITE_WEBPAY_ENABLED=false
```

### Variables Explicadas
- **VITE_API_URL**: URL base de la API del backend (requerido)
- **VITE_PAYMENTS_PROVIDER**: Proveedor de pagos (default: `webpay`)
- **VITE_WEBPAY_ENABLED**: Habilitar botón de pago Webpay (default: `false` - placeholder)

## Notas

- El carrito persiste en localStorage (usuarios logueados) o sessionStorage (invitados)
- Envío gratis aplica cuando el subtotal >= CLP 50.000
- Las rutas admin requieren rol `admin`
- Los formularios usan React Hook Form para validación
- Checkout: Invitados usan sessionStorage, usuarios logueados usan localStorage
- Pago: Actualmente es placeholder (Webpay deshabilitado), preparado para integración futura
- Password Reset: Las páginas `ForgotPassword` y `ResetPassword` están implementadas en el frontend pero los endpoints del backend aún no están disponibles (se muestran como placeholder)

## Seguridad

### ✅ Medidas Implementadas
- Dependencias actualizadas a versiones seguras
- Variables de entorno para configuración (no hardcodeadas)
- Interceptor Axios para manejo seguro de tokens
- Validación de autenticación en rutas protegidas
- Headers CORS/CSRF configurados correctamente

### 📋 Auditoría de Seguridad
- Ejecutar `npm audit` regularmente
- Ver `SECURITY_REMEDIATION_PLAN.md` para detalles de la última remediación
- Ver `CHANGELOG.md` para historial de cambios de seguridad

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





