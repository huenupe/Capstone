# Changelog - Frontend CondorShop

## [2025-01-XX] - Checkout + Auth — Placeholders, Validaciones, Resumen, Dirección, Pago (Webpay placeholder)

### 🎨 UX Global de Formularios
- ✅ **Placeholders consistentes**: Todos los formularios ahora tienen placeholders descriptivos en español
- ✅ **Helper texts**: Agregado soporte para textos de ayuda debajo de los campos
- ✅ **Accesibilidad mejorada**: ARIA roles, labels y mensajes de error accesibles
- ✅ **Focus visible**: Navegación por teclado mejorada

### ✅ Validaciones de Datos
- ✅ **Nombres/Apellidos**: Solo letras y espacios (sin números ni símbolos)
- ✅ **Email**: Validación con regex mejorada
- ✅ **Teléfono Chile**: Formato exacto +569 + 8 dígitos (12 caracteres totales)
- ✅ **Contraseña**: Mínimo 8 caracteres
- ✅ **Errores inline**: Todos los errores se muestran debajo del campo correspondiente (rojo)

### 🔐 Login + Recuperación de Contraseña
- ✅ **Errores inline**: Errores de email/contraseña se muestran bajo el campo correspondiente
- ✅ **Enlace "¿Olvidaste tu contraseña?"**: Agregado en pantalla de login
- ✅ **Página ForgotPassword**: Formulario para solicitar reset de contraseña
- ✅ **Página ResetPassword**: Formulario para establecer nueva contraseña desde token
- ⚠️ **Backend pendiente**: Flujo FE listo, esperando implementación BE de envío de emails

### 🛒 Carrito — Textos y Resumen
- ✅ **Botón actualizado**: "Proceder al Checkout" → "Continuar compra"
- ✅ **Título del resumen**: "Resumen" → "Resumen de la compra"
- ✅ **Estructura del resumen**:
  - Productos (N): Total de productos
  - Descuentos: Total de descuentos aplicados
  - Entregas: Costo dinámico (Gratis si retiro o envío gratis)
  - Total: Monto final

### 📍 Paso 2 — Dirección / Entrega (Restructurado)
- ✅ **Layout izquierda/derecha**: 
  - Izquierda: Formulario de dirección + métodos de entrega
  - Derecha: Resumen de la compra actualizado
- ✅ **Métodos de entrega**:
  - Retiro en punto: Gratis, selector de tienda (mock), fecha disponible (mock)
  - Envío a domicilio: Costo dinámico, fecha estimada y franja horaria (mock)
- ✅ **Campos de dirección mejorados**:
  - Región (select)
  - Comuna
  - Calle
  - Número
  - Dpto/Casa/Oficina (opcional)
  - Código Postal
- ✅ **Placeholders consistentes**: Todos los campos tienen placeholders descriptivos
- ✅ **Botón CTA**: "Ir a pagar" en lugar de "Continuar"

### 👤 Flujo de Invitado
- ✅ **Stepper de 4 pasos**: Carro → Datos → Dirección → Pago
- ✅ **Stepper de 3 pasos (logueado)**: Carro → Dirección → Pago
- ✅ **Paso 2 (invitado)**: Datos mínimos (Nombre, Apellido, Email, Teléfono) con validaciones
- ✅ **Persistencia**: Datos del invitado en sessionStorage hasta completar orden

### 💳 Paso 3 — Pago (Webpay placeholder)
- ✅ **Nuevo componente StepPayment**: Página dedicada para selección de método de pago
- ✅ **Webpay Plus**: 
  - Seleccionable (radio button)
  - Descripción completa
  - Logos de tarjetas
  - Texto de confianza sobre seguridad
- ✅ **Otros métodos**: Deshabilitado con tooltip "Disponible próximamente"
- ✅ **Botón Continuar**: Deshabilitado con tooltip "Próximamente"
- ✅ **Variables de entorno**:
  - `VITE_PAYMENTS_PROVIDER=webpay`
  - `VITE_WEBPAY_ENABLED=false` (placeholder)
- ✅ **checkoutSlice**: Nuevo store para manejar estado de pago (paymentMethod, canPay, deliveryMethod)

### 🔄 Estado, Persistencia y Consistencia
- ✅ **sessionStorage para invitados**: Datos del checkout se guardan en sessionStorage
- ✅ **localStorage para logueados**: Datos del checkout se guardan en localStorage
- ✅ **checkoutSlice (Zustand)**: Nueva fuente de verdad para estado del checkout
- ✅ **Resumen consistente**: Mismos montos en Carro, Paso 2 y Paso 3
- ✅ **CheckoutStepper**: Componente reutilizable que muestra pasos correctos según autenticación

### 🔒 Seguridad
- ✅ **No recolección de datos de tarjetas**: Placeholder preparado, sin recolección real
- ✅ **CORS/CSRF**: Ya configurados correctamente
- ✅ **Validaciones del lado del cliente**: Robustas y consistentes

### 🧩 Componentes Nuevos
- ✅ **CheckoutStepper**: Componente reutilizable para mostrar progreso del checkout
- ✅ **StepPayment**: Nueva página para selección de método de pago
- ✅ **ForgotPassword**: Página para solicitar reset de contraseña
- ✅ **ResetPassword**: Página para establecer nueva contraseña

### 📝 Utilidades
- ✅ **validations.js**: Funciones de validación reutilizables
  - `validateOnlyLetters`: Solo letras y espacios
  - `validateChileanPhone`: Formato +569 + 8 dígitos
  - `validateEmail`: Email válido
  - `validatePassword`: Mínimo 8 caracteres
- ✅ **storage.js mejorado**: Soporte para sessionStorage y localStorage

### 🎯 Cambios en Componentes Existentes
- ✅ **TextField**: Agregado soporte para `helperText` y mejoras de accesibilidad
- ✅ **StepCustomer**: Validaciones mejoradas, placeholders, flujo para invitado
- ✅ **StepAddress**: Restructurado con layout izquierda/derecha, métodos de entrega
- ✅ **StepReview**: Actualizado para usar storage correcto según autenticación
- ✅ **Cart**: Botón y resumen actualizados
- ✅ **Login**: Errores inline, enlace a recuperación
- ✅ **Register**: Validaciones mejoradas, campo teléfono agregado

### 📋 Tareas Backend Pendientes (documentadas)
- ⚠️ **Reset Password**: Implementar endpoints de reset de contraseña
- ⚠️ **Email**: Configurar EMAIL_BACKEND, DEFAULT_FROM_EMAIL y credenciales
- ⚠️ **Plantillas de email**: Crear templates en español para reset password
- ⚠️ **Tokens temporales**: Implementar generación y validación de tokens de reset
- ⚠️ **Webpay**: Preparar integración cuando esté lista (FE ya tiene placeholder)

### 🧪 QA / Criterios de Aceptación
- ✅ Formularios: Placeholders y helper texts en todos los inputs
- ✅ Validaciones: Nombres (solo letras), teléfono (+569 + 8 dígitos), email válido
- ✅ Login: Errores bajo campo, enlace "¿Olvidaste tu contraseña?" funcional
- ✅ Reset password: Pantallas FE listas (BE pendiente)
- ✅ Carrito: "Continuar compra", "Resumen de la compra" con estructura correcta
- ✅ Paso 2: Selector de dirección, métodos de entrega, resumen actualizado
- ✅ Invitado: Stepper de 4 pasos, datos mínimos en paso 2
- ✅ Paso 3 (Pago): Webpay seleccionable, "Otros" deshabilitado, botón deshabilitado
- ✅ Accesibilidad: Navegación por teclado, roles ARIA, focus visible
- ✅ Responsive: Layout funciona en mobile y desktop

### 📦 Variables de Entorno Nuevas
```env
VITE_PAYMENTS_PROVIDER=webpay
VITE_WEBPAY_ENABLED=false
```

---

## [2025-01-27] - Remediación de Vulnerabilidades

### 🔒 Seguridad

#### Actualización de Dependencias
- **Vite**: `5.4.6` → `7.1.12` (Major update)
  - **Motivo**: Vulnerabilidad en esbuild (GHSA-67mh-4wv8-2f99)
  - **Severidad**: Moderate (CVSS 5.3)
  - **Impacto**: Solo afecta servidor de desarrollo, no producción
  - **Estado**: ✅ Resuelto - 0 vulnerabilidades detectadas

- **@vitejs/plugin-react**: `4.3.1` → `4.7.0` (Actualización automática)
  - **Motivo**: Compatibilidad con Vite 7
  - **Estado**: ✅ Compatible y funcionando

#### Vulnerabilidades Corregidas
- ✅ **esbuild**: Actualizado de `0.21.5` (vulnerable) → `0.25.12` (seguro)
- ✅ **Vite**: Actualizado de `5.4.6` (vulnerable) → `7.1.12` (seguro)
- ✅ **Auditoría**: `npm audit` reporta 0 vulnerabilidades

### 🔧 Correcciones

#### Endpoints API - Alineación con Backend
- **Corregido**: `getUserOrders()` ahora usa `/api/orders/` (endpoint correcto)
  - Antes: Intentaba `/api/users/orders` (no existe)
  - Ahora: Usa `/api/orders/` según documentación del backend

- **Corregido**: `createOrder()` ahora usa `/api/checkout/create`
  - Antes: Usaba `/api/orders/create`
  - Ahora: Usa `/api/checkout/create` según documentación del backend

#### Calidad de Código
- **Eliminados**: Imports no utilizados
  - `user` en Header.jsx
  - `Button` en Modal.jsx
  - `useEffect` en Toast.jsx
  - `Select` en Admin/Orders.jsx
  - `setLoading`, `toast` en StepCustomer y StepAddress

- **Corregidos**: Comillas no escapadas en Home.jsx
  - `"` → `&quot;` para cumplir con react/no-unescaped-entities

### ✅ Validaciones

#### Build y Desarrollo
- ✅ `npm run build` ejecuta correctamente con Vite 7.1.12
- ✅ Build generado: `dist/` con assets optimizados
- ✅ Tiempo de build: ~1.56s (mejorado)

#### Linter
- ✅ 0 errores críticos
- ⚠️ 14 warnings (dependencias en useEffect - aceptables)
- ✅ Reglas de ESLint cumplidas

#### Compatibilidad
- ✅ Node.js v22.19.0 compatible con Vite 7
- ✅ React 18.3.1 compatible
- ✅ Todas las dependencias compatibles

### 📝 Documentación

#### Archivos Actualizados
- ✅ `SECURITY_REMEDIATION_PLAN.md` - Plan completo de remediación
- ✅ `README.md` - Actualizado con versiones soportadas
- ✅ `CHANGELOG.md` - Este archivo

#### Notas de Seguridad
- La vulnerabilidad de esbuild solo afectaba al servidor de desarrollo
- No hay impacto en producción (build usa esbuild empaquetado)
- Todas las vulnerabilidades han sido resueltas

### 🔗 Alineación con Backend

#### Endpoints Verificados
- ✅ `/api/auth/register` - POST
- ✅ `/api/auth/login` - POST
- ✅ `/api/users/profile` - GET/PATCH
- ✅ `/api/products/` - GET (con filtros)
- ✅ `/api/products/{slug}/` - GET
- ✅ `/api/products/categories/` - GET
- ✅ `/api/cart/` - GET
- ✅ `/api/cart/add` - POST
- ✅ `/api/cart/items/{id}` - PATCH/DELETE
- ✅ `/api/checkout/create` - POST (corregido)
- ✅ `/api/orders/` - GET (corregido)
- ✅ `/api/admin/products` - CRUD
- ✅ `/api/admin/orders` - GET/PATCH

#### Headers y Autenticación
- ✅ `Authorization: Bearer <token>` implementado
- ✅ `X-Session-Token` para carrito de invitados
- ✅ `Content-Type: multipart/form-data` para imágenes

#### CORS/CSRF
- ✅ Frontend en `http://localhost:5173` coincide con backend
- ✅ No se requieren cambios en configuración

---

## Versiones Soportadas

### Herramientas Principales
- **Node.js**: 18+ (recomendado: 20+ LTS)
- **npm**: 9+ (viene con Node.js)
- **Vite**: 7.1.12+
- **React**: 18.3.1+

### Dependencias de Producción
- **react**: ^18.3.1
- **react-dom**: ^18.3.1
- **react-router-dom**: ^6.26.0
- **axios**: ^1.7.7
- **zustand**: ^4.5.5
- **react-hook-form**: ^7.53.0

### Dependencias de Desarrollo
- **vite**: ^7.1.12
- **@vitejs/plugin-react**: ^4.7.0
- **tailwindcss**: ^3.4.13
- **eslint**: ^8.57.0
- **autoprefixer**: ^10.4.20
- **postcss**: ^8.4.47

---

## Notas Importantes

### Variables de Entorno
- **VITE_API_URL**: URL base de la API (default: `http://localhost:8000/api`)
- Crear archivo `.env` en la raíz de `frontend/` con:
  ```
  VITE_API_URL=http://localhost:8000/api
  ```

### Desarrollo
```bash
npm install    # Instalar dependencias
npm run dev    # Servidor de desarrollo (http://localhost:5173)
npm run build  # Build de producción
npm run preview # Preview del build
npm run lint   # Ejecutar linter
```

### Seguridad
- ✅ Todas las vulnerabilidades conocidas resueltas
- ✅ Dependencias actualizadas a versiones seguras
- ✅ No hay valores sensibles hardcodeados
- ✅ URLs de API se leen de variables de entorno

---

**Fecha de Actualización:** 2025-01-27  
**Responsable:** Arquitecto Frontend + SecOps  
**Estado:** ✅ COMPLETADO - LISTO PARA PRODUCCIÓN

