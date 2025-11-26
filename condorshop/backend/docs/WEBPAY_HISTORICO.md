# 📚 Historial de Implementación Webpay Plus - CondorShop

**Última actualización:** Noviembre 2025  
**Estado:** Documentación histórica consolidada

---

## 📋 Índice

1. [Análisis Completo de Implementación](#1-análisis-completo-de-implementación)
2. [Documentación de Implementación](#2-documentación-de-implementación)
3. [Solución Error 503 Detallada](#3-solución-error-503-detallada)
4. [Solución Error 503 (Guía Rápida)](#4-solución-error-503-guía-rápida)
5. [Guía de Testing Webpay](#5-guía-de-testing-webpay)

---

## 1. Análisis Completo de Implementación

**Fecha:** Noviembre 2025  
**Proyecto:** CondorShop E-commerce Backend  
**Stack:** Django 5.2.8 + DRF 3.16.1 + PostgreSQL  
**SDK de Pago:** transbank-sdk 3.0.0  
**Ambiente:** Desarrollo (Integration)

### Arquitectura de la Implementación

#### Backend (Django)

**Estructura de Archivos Clave:**
```
condorshop/backend/
├── apps/orders/
│   ├── services.py          # WebpayService class + inicialización global
│   ├── views.py             # Endpoints de API (initiate_webpay_payment, webpay_return)
│   ├── urls.py              # Rutas de checkout/orders
│   ├── payment_urls.py      # Rutas de callbacks de Webpay
│   └── models.py            # PaymentTransaction, Payment, Order
├── condorshop_api/
│   ├── settings.py          # WEBPAY_CONFIG
│   └── urls.py              # Inclusión de rutas
└── requirements.txt         # transbank-sdk==3.0.0
```

#### Configuración (settings.py)

```python
WEBPAY_CONFIG = {
    'ENVIRONMENT': env('WEBPAY_ENVIRONMENT', default='integration'),
    'COMMERCE_CODE': env('WEBPAY_COMMERCE_CODE', default='597055555532'),
    'API_KEY': env('WEBPAY_API_KEY', default='...'),
    'RETURN_URL': env('WEBPAY_RETURN_URL', default='http://localhost:8000/api/payments/return/'),
    'FINAL_URL': env('WEBPAY_FINAL_URL', default='http://localhost:5173/payment/result'),
}
```

#### Inicialización del Servicio (services.py)

**Importación Condicional:**
```python
try:
    from transbank.error.transbank_error import TransbankError
    from transbank.webpay.webpay_plus.transaction import Transaction
    TRANSBANK_AVAILABLE = True
except ImportError:
    TRANSBANK_AVAILABLE = False
    logger.warning("transbank-sdk no está instalado. Webpay no funcionará.")
```

**Instancia Global:**
```python
if TRANSBANK_AVAILABLE:
    try:
        webpay_service = WebpayService()
        logger.info("WebpayService inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar WebpayService: {str(e)}", exc_info=True)
        webpay_service = None
else:
    webpay_service = None
```

**⚠️ PROBLEMA CRÍTICO:** Esta instancia global se crea **al importar el módulo**, es decir, cuando Django carga la aplicación. Si en ese momento `transbank-sdk` no está disponible o hay un error, `webpay_service` queda como `None` y **no se actualiza automáticamente**.

#### Endpoints de API

**Endpoint 1: Iniciar Pago** (`initiate_webpay_payment`)
- **Ruta:** `POST /api/checkout/{order_id}/pay/` o `POST /api/orders/{order_id}/pay/`
- **Permisos:** `AllowAny` (permite invitados)
- **Lógica:**
  1. Verifica si `webpay_service is None`
  2. Si es `None` pero `TRANSBANK_AVAILABLE=True`, intenta re-inicializar
  3. Valida orden (debe estar en estado `PENDING`)
  4. Valida propiedad (usuario autenticado o session_token)
  5. Llama a `webpay_service.create_transaction(order)`
  6. Retorna `{token, url, order_id, amount}`

**Endpoint 2: Callback de Retorno** (`webpay_return`)
- **Ruta:** `GET/POST /api/payments/return/?token_ws=XXX`
- **Permisos:** `AllowAny` + `@csrf_exempt`
- **Lógica:**
  1. Obtiene `token_ws` de query params o POST
  2. Llama a `webpay_service.confirm_transaction(token)`
  3. Redirige al frontend con `status=success|failed`

#### Métodos del Servicio

**`create_transaction(order)`**:
- Valida que la orden no esté pagada
- Verifica si hay transacción pendiente (reutiliza token)
- Genera `buy_order` único
- Llama a `Transaction.create()` del SDK
- Crea `PaymentTransaction` en BD
- Retorna `(success, token, data)`

**`confirm_transaction(token)`**:
- Busca `PaymentTransaction` por token
- Llama a `Transaction.commit(token)` del SDK
- Si `response_code == 0`: Pago aprobado
  - Actualiza orden a `PAID`
  - Actualiza payment a `CAPTURED`
  - Decrementa stock de productos
- Si `response_code != 0`: Pago rechazado
  - Actualiza orden a `FAILED`
  - Libera stock reservado
- Retorna `(success, message, data)`

### Frontend (React)

**Estructura de Archivos:**
```
condorshop/frontend/
├── src/
│   ├── services/
│   │   └── paymentsService.js    # Cliente de API para Webpay
│   ├── pages/
│   │   ├── Orders.jsx             # Lista de pedidos + botón "Pagar Ahora"
│   │   └── PaymentResultPage.jsx  # Página de resultado de pago
│   └── routes/
│       └── AppRoutes.jsx          # Ruta /payment/result
```

**Servicio de Pagos (paymentsService.js):**
- `initiateWebpayPayment(orderId)`: Llama a `POST /api/checkout/{orderId}/pay/`
- `redirectToWebpay(token, url)`: Crea formulario HTML y redirige a Webpay
- `getPaymentStatus(orderId)`: Consulta estado de pago

### Flujo Completo de Pago

**Flujo Normal (Éxito):**
1. Usuario hace click en "Pagar Ahora"
2. Frontend: `POST /api/checkout/{order_id}/pay/`
3. Backend: `initiate_webpay_payment()` → `webpay_service.create_transaction(order)`
4. Backend: Crea transacción en Webpay → recibe `token` y `url`
5. Backend: Retorna `{token, url, order_id, amount}` al frontend
6. Frontend: Crea formulario HTML y redirige a Webpay (POST con `token_ws`)
7. Usuario: Completa pago en Webpay
8. Webpay: Redirige a `RETURN_URL` (`/api/payments/return/?token_ws=XXX`)
9. Backend: `webpay_return()` → `webpay_service.confirm_transaction(token)`
10. Backend: Confirma pago, actualiza orden a `PAID`, decrementa stock
11. Backend: Redirige a `FINAL_URL` (`/payment/result?status=success&order_id=X`)
12. Frontend: `PaymentResultPage` muestra resultado exitoso

**Flujo con Error 503:**
1. Usuario hace click en "Pagar Ahora"
2. Frontend: `POST /api/checkout/{order_id}/pay/`
3. Backend: `initiate_webpay_payment()` detecta `webpay_service is None`
4. Backend: Intenta re-inicializar (si `TRANSBANK_AVAILABLE=True`)
5. Backend: Si falla, retorna `503 Service Unavailable`
6. Frontend: Muestra error "Webpay no está disponible"

### Problemas Identificados

**Problema Principal: Error 503 Service Unavailable**

**Síntoma:**
```
POST http://localhost:8000/api/checkout/1/pay/
Status: 503 Service Unavailable
Response: {"error": "Webpay no está disponible. Contacta al administrador."}
```

**Causa Raíz:**
El servidor Django retorna 503 porque `webpay_service` es `None` cuando se ejecuta la vista.

**Evidencia:**
1. ✅ `transbank-sdk==3.0.0` está instalado (verificado con `pip list`)
2. ✅ El módulo se puede importar correctamente (verificado con script independiente)
3. ✅ `WebpayService` se puede crear cuando se ejecuta directamente
4. ❌ **PERO:** El servidor Django tiene `webpay_service = None`

**Hipótesis del Problema:**
1. El servidor Django se inició ANTES de instalar `transbank-sdk`
2. Error silencioso durante la inicialización
3. Problema de importación en el contexto de Django

---

## 2. Documentación de Implementación

**Fecha de Implementación:** Noviembre 2025  
**Versión:** 1.0  
**Estado:** ✅ Implementado

### Dependencias Instaladas

**Backend (Python/Django):**
```txt
transbank-sdk==3.0.0
setuptools==80.9.0  # Necesario para Python 3.12+ (proporciona distutils)
```

**Nota:** `setuptools` es necesario porque Python 3.12+ removió `distutils` del stdlib, y `transbank-sdk` depende de él.

### Configuración

**Variables de Entorno (.env) - Backend:**
```env
# Webpay Plus Configuration
WEBPAY_ENVIRONMENT=integration
WEBPAY_COMMERCE_CODE=597055555532
WEBPAY_API_KEY=579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C
WEBPAY_RETURN_URL=http://localhost:8000/api/payments/return/
WEBPAY_FINAL_URL=http://localhost:5173/payment/result
```

**Variables de Entorno (.env) - Frontend:**
```env
VITE_WEBPAY_ENABLED=true
VITE_API_URL=http://localhost:8000/api
```

### Modelos de Base de Datos

**PaymentTransaction:**
- `order` (ForeignKey → Order)
- `payment_method` (CharField, default='webpay')
- `status` (CharField: 'pending', 'approved', 'rejected', 'failed', 'cancelled')
- `amount` (PositiveIntegerField)
- `webpay_token` (CharField, unique=True)
- `webpay_buy_order` (CharField)
- `webpay_authorization_code` (CharField)
- `webpay_transaction_date` (DateTimeField)
- `card_last_four` (CharField, max_length=4)
- `card_brand` (CharField)
- `gateway_response` (JSONField)

**Índices:**
- `idx_payment_tx_order` (order)
- `idx_payment_tx_status` (status)
- `idx_payment_webpay_token` (webpay_token)
- `idx_payment_tx_created` (created_at)

### Backend - Implementación

#### WebpayService (Servicio Principal)

**Métodos Principales:**

**`__init__(self)`:**
- Verifica disponibilidad de `transbank-sdk`
- Configura ambiente (producción/integración)
- Establece credenciales según ambiente

**`create_transaction(self, order: Order)`:**
- Valida que la orden no esté pagada
- Verifica transacciones pendientes (reutiliza token si existe)
- Genera `buy_order` único: `ORDER-{order_id}-{timestamp}`
- Genera `session_id`: `SESSION-{order_id}`
- Convierte monto a entero (pesos chilenos sin decimales)
- Llama a `Transaction.create()` del SDK
- Crea `PaymentTransaction` en BD
- Retorna `(success, token, data)`

**`confirm_transaction(self, token: str)`:**
- Busca `PaymentTransaction` por token
- Llama a `Transaction.commit(token)` del SDK
- Si `response_code == 0` (aprobado):
  - Actualiza transacción a `approved`
  - Actualiza `Payment` a `CAPTURED`
  - Actualiza `Order` a `PAID`
  - Decrementa stock de productos (`product.confirm_sale()`)
- Si `response_code != 0` (rechazado):
  - Actualiza transacción a `rejected`
  - Actualiza `Payment` a `FAILED`
  - Actualiza `Order` a `FAILED`
  - Libera stock reservado (`product.release_stock()`)
- Retorna `(success, message, data)`

### Frontend - Implementación

#### Servicio de Pagos

**`initiateWebpayPayment(orderId)`:**
- Llama a `POST /api/checkout/{orderId}/pay/`
- Retorna `{token, url, order_id, amount}`

**`getPaymentStatus(orderId)`:**
- Llama a `GET /api/payments/status/{orderId}/`
- Retorna estado de la orden y transacción

**`redirectToWebpay(token, url)`:**
- Crea formulario HTML dinámico
- Hace POST a Webpay con `token_ws`
- Redirige al usuario a Webpay

#### Componentes

**Orders.jsx - Botón "Pagar Ahora":**
- Función `handleRetryPayment`:
  1. Verifica `VITE_WEBPAY_ENABLED === 'true'`
  2. Llama a `paymentsService.initiateWebpayPayment(orderId)`
  3. Guarda `order_id` en `sessionStorage`
  4. Muestra toast de éxito
  5. Redirige a Webpay usando `paymentsService.redirectToWebpay()`

**PaymentResultPage.jsx - Página de Resultado:**
- Ruta: `/payment/result?status=success&order_id=123`
- Funcionalidad:
  1. Lee `status` y `order_id` de query params
  2. Consulta estado de pago con `paymentsService.getPaymentStatus(orderId)`
  3. Muestra:
     - **Éxito:** Mensaje de confirmación, número de orden, monto, código de autorización, últimos 4 dígitos de tarjeta
     - **Fallo:** Mensaje de error, opción de reintentar
  4. Limpia `sessionStorage`

### Seguridad y Validaciones

**Validaciones Implementadas:**
1. Orden debe estar en estado PENDING
2. Validación de propiedad (usuario autenticado o `X-Session-Token` para invitados)
3. No pagar orden ya pagada
4. Reutilización de tokens pendientes
5. Validación de producción (no permite `localhost` en URLs cuando `ENVIRONMENT='production'`)

**Datos Sensibles:**
- **NO se almacenan:** Números completos de tarjetas, CVV/CVC, datos sensibles de tarjetas
- **SÍ se almacenan (seguro):** Últimos 4 dígitos de tarjeta, marca de tarjeta, código de autorización, token de Webpay

### Gestión de Stock

**Reserva de Stock:**
- El stock se reserva cuando se crea la orden (estado `PENDING`)
- Método: `product.reserve_stock(quantity)`

**Confirmación de Venta:**
- Cuando el pago es aprobado (`response_code == 0`):
  ```python
  product.confirm_sale(order_item.quantity)
  ```
- Decrementa el stock definitivamente

**Liberación de Stock:**
- Cuando el pago es rechazado:
  ```python
  product.release_stock(
      quantity=order_item.quantity,
      reason='Payment rejected',
      reference_id=order.id
  )
  ```
- Libera el stock reservado

### Problemas Encontrados y Soluciones

**Problema 1: ModuleNotFoundError: No module named 'transbank'**
- **Causa:** `transbank-sdk` instalado en Python global, no en entorno virtual
- **Solución:** Instalar en entorno virtual:
  ```powershell
  .\.venv\Scripts\python.exe -m pip install transbank-sdk==3.0.0
  ```

**Problema 2: No module named 'distutils'**
- **Causa:** Python 3.12+ removió `distutils`, `transbank-sdk` depende de él
- **Solución:** Instalar `setuptools`:
  ```powershell
  .\.venv\Scripts\python.exe -m pip install setuptools
  ```

**Problema 3: TypeError: Transaction.create() missing 1 required positional argument: 'self'**
- **Causa:** `Transaction.create()` se llamaba como método de instancia
- **Solución:** Llamar directamente en la clase:
  ```python
  # ❌ INCORRECTO:
  response = self.Transaction.create(...)
  
  # ✅ CORRECTO:
  _, Transaction = _get_transbank_imports()
  response = Transaction.create(...)
  ```

---

## 3. Solución Error 503 Detallada

**Error Observado:**
```
POST http://localhost:8000/api/checkout/1/pay/
Status: 503 Service Unavailable
Error: "Webpay no está disponible. Contacta al administrador."
```

### Causa Raíz Identificada

El servidor Django está retornando 503 porque `webpay_service is None` cuando se ejecuta la vista `initiate_webpay_payment`.

**Verificación realizada:**
- ✅ `transbank-sdk==3.0.0` está instalado
- ✅ El módulo se puede importar correctamente
- ✅ `WebpayService` se puede crear cuando se ejecuta directamente
- ❌ **PERO:** El servidor Django tiene `webpay_service = None`

### Solución Implementada

#### 1. Mejora en la Inicialización del Servicio

**Archivo:** `apps/orders/services.py`

Se agregó manejo de errores robusto al crear la instancia global:

```python
# Instancia global del servicio
if TRANSBANK_AVAILABLE:
    try:
        webpay_service = WebpayService()
        logger.info("WebpayService inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar WebpayService: {str(e)}", exc_info=True)
        webpay_service = None
        logger.warning("WebpayService no disponible debido a error en inicialización.")
else:
    webpay_service = None
    logger.warning("WebpayService no disponible. Instala transbank-sdk para habilitarlo.")
```

**Beneficios:**
- Captura errores durante la inicialización
- Registra logs detallados para debugging
- Evita que el servidor falle silenciosamente

#### 2. Re-inicialización Automática en la Vista

**Archivo:** `apps/orders/views.py`

Se agregó lógica para intentar re-inicializar el servicio si está disponible pero no inicializado:

```python
if webpay_service is None:
    logger.error(f"Intento de pago con webpay_service=None. TRANSBANK_AVAILABLE={TRANSBANK_AVAILABLE}")
    # Intentar re-inicializar si TRANSBANK_AVAILABLE es True
    if TRANSBANK_AVAILABLE:
        try:
            from .services import WebpayService
            global webpay_service
            webpay_service = WebpayService()
            logger.info("WebpayService re-inicializado exitosamente")
        except Exception as e:
            logger.error(f"Error al re-inicializar WebpayService: {str(e)}", exc_info=True)
            return Response({
                'error': 'Webpay no está disponible. Contacta al administrador.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
```

**Beneficios:**
- Intenta recuperarse automáticamente si el servicio no estaba inicializado
- Registra información detallada para debugging
- Solo retorna 503 si realmente no se puede inicializar

### Acción Requerida: Reiniciar Servidor Django

**⚠️ CRÍTICO:** El servidor Django debe reiniciarse para que los cambios surtan efecto.

**Pasos:**
1. Detén el servidor Django (Ctrl+C)
2. Inicia nuevamente: `python manage.py runserver`
3. Verifica los logs al iniciar:
   - ✅ Debe aparecer: `INFO WebpayService inicializado correctamente`
   - ❌ NO debe aparecer: `WARNING WebpayService no disponible`
4. Prueba nuevamente desde el frontend

### Verificación Post-Reinicio

**1. Verificar logs del servidor:**
Al iniciar el servidor, busca en los logs:
```
INFO WebpayService inicializado correctamente
```

**2. Probar el endpoint directamente:**
```powershell
curl -X POST http://localhost:8000/api/checkout/1/pay/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Debe retornar: `200 OK` con `token` y `url` de Webpay

**3. Verificar desde el frontend:**
1. Recarga la página de pedidos
2. Click en "Pagar Ahora"
3. **Debe redirigir a Webpay** (no debe mostrar error 503)

### Logs a Revisar

**Al iniciar el servidor:**
```
INFO WebpayService inicializado correctamente
```

**Si hay un error:**
```
ERROR Error al inicializar WebpayService: ...
WARNING WebpayService no disponible debido a error en inicialización.
```

**Al intentar pagar (si webpay_service era None):**
```
ERROR Intento de pago con webpay_service=None. TRANSBANK_AVAILABLE=True
INFO WebpayService re-inicializado exitosamente
```

### Si el Problema Persiste Después de Reiniciar

**Causa 1: Error en la inicialización**
Revisa los logs del servidor para ver el error específico:
```
ERROR Error al inicializar WebpayService: ...
```

**Causa 2: Problema con la configuración**
Verifica que las variables de entorno estén correctas:
```bash
cd condorshop\backend
python verify_transbank_import.py
```

**Causa 3: Múltiples procesos de Django**
Asegúrate de que solo hay un proceso de Django corriendo:
```powershell
Get-Process python | Where-Object {$_.Path -like "*python*"}
```

---

## 4. Solución Error 503 (Guía Rápida)

**Error:** `503 Service Unavailable` al intentar iniciar pago con Webpay  
**Mensaje:** "Webpay no está disponible. Contacta al administrador."

**Causa Raíz:** El servidor Django se inició antes de que `transbank-sdk` estuviera instalado, o el módulo no se cargó correctamente.

### Solución Paso a Paso

#### Paso 1: Verificar que transbank-sdk esté instalado

```powershell
cd condorshop\backend
pip list | Select-String transbank
```

**Debe mostrar:** `transbank-sdk 3.0.0`

Si no está instalado:
```powershell
pip install transbank-sdk==3.0.0
```

#### Paso 2: Verificar que se puede importar

```powershell
cd condorshop\backend
python verify_transbank_import.py
```

**Debe mostrar:**
```
[OK] transbank-sdk se puede importar correctamente
[OK] WebpayService está disponible
[OK] Configuración correcta
```

#### Paso 3: REINICIAR el servidor Django

**⚠️ CRÍTICO:** El servidor Django debe reiniciarse para cargar el módulo.

1. **Detén el servidor Django:**
   - En la terminal donde corre `python manage.py runserver`
   - Presiona `Ctrl+C`

2. **Inicia nuevamente:**
   ```powershell
   cd condorshop\backend
   python manage.py runserver
   ```

3. **Verifica que no haya warnings:**
   - NO debe aparecer: `WARNING transbank-sdk no está instalado`
   - NO debe aparecer: `WARNING WebpayService no disponible`

#### Paso 4: Verificar en el código

El código ya está correctamente implementado con manejo de errores robusto y re-inicialización automática.

### Verificación Post-Solución

**1. Verificar logs del servidor Django:**
Al iniciar el servidor, NO debe aparecer:
```
WARNING transbank-sdk no está instalado. Webpay no funcionará.
WARNING WebpayService no disponible. Instala transbank-sdk para habilitarlo.
```

**2. Probar el endpoint:**
```powershell
curl -X POST http://localhost:8000/api/checkout/1/pay/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Debe retornar:** `200 OK` con `token` y `url` de Webpay

**3. Probar desde el frontend:**
1. Agrega productos al carrito
2. Completa checkout
3. Click en "Crear Pedido"
4. **Debe redirigir a Webpay** (no debe mostrar error 503)

### Checklist de Verificación

- [ ] `transbank-sdk==3.0.0` está instalado
- [ ] `python verify_transbank_import.py` muestra todo OK
- [ ] Servidor Django reiniciado
- [ ] No hay warnings en los logs del servidor
- [ ] El endpoint `/api/checkout/{id}/pay/` responde correctamente
- [ ] El frontend puede iniciar pagos sin error 503

### Si el Problema Persiste

**Causa 1: Entorno virtual diferente**
Si usas un entorno virtual, asegúrate de activarlo:
```powershell
.\venv\Scripts\Activate.ps1
pip install transbank-sdk==3.0.0
```

**Causa 2: Múltiples versiones de Python**
Verifica qué Python está usando Django:
```powershell
cd condorshop\backend
python --version
python -c "import sys; print(sys.executable)"
```

Asegúrate de instalar en el mismo Python:
```powershell
python -m pip install transbank-sdk==3.0.0
```

**Causa 3: Caché de módulos Python**
Limpia el caché de Python:
```powershell
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
```

### Notas Importantes

1. **El servidor Django debe reiniciarse** después de instalar nuevos paquetes
2. **transbank-sdk** debe estar en `requirements.txt` (ya está)
3. **El código maneja correctamente** el caso cuando el servicio no está disponible
4. **Los warnings en logs** son informativos y ayudan a diagnosticar

---

## 5. Guía de Testing Webpay

### Información de Tarjetas de Prueba

#### ✅ Transacción Aprobada
```
Número: 4051 8856 0000 0002
CVV: 123
Fecha: Cualquier fecha futura (ej: 12/25)
RUT: 11.111.111-1
```

#### ❌ Transacción Rechazada
```
Número: 4051 8842 3993 7763
CVV: 123
Fecha: Cualquier fecha futura (ej: 12/25)
RUT: 11.111.111-1
```

#### ⏰ Timeout (para probar cancelación)
No completar el pago y cerrar la ventana de Webpay

### Checklist de Pruebas

#### Test 1: Flujo Completo Exitoso
- [ ] Agregar productos al carrito
- [ ] Ir a checkout
- [ ] Completar datos de envío
- [ ] Crear orden (verifica que se cree en estado PENDING)
- [ ] Redirige automáticamente a Webpay
- [ ] Usar tarjeta aprobada (4051 8856 0000 0002)
- [ ] Verificar redirección a /payment/result?status=success
- [ ] Verificar que la orden cambió a PAID
- [ ] Verificar que se decrementó el stock
- [ ] Verificar auditoría en admin

#### Test 2: Pago Rechazado
- [ ] Crear orden
- [ ] Usar tarjeta rechazada (4051 8842 3993 7763)
- [ ] Verificar redirección a /payment/result?status=failed
- [ ] Verificar que la orden cambió a FAILED
- [ ] Verificar que se liberó el stock

#### Test 3: Usuario Invitado
- [ ] NO iniciar sesión
- [ ] Agregar productos (usa session_token)
- [ ] Completar checkout como invitado
- [ ] Pagar con Webpay
- [ ] Verificar que funciona sin usuario autenticado

#### Test 4: Reintentar Pago
- [ ] Crear orden
- [ ] Rechazar pago
- [ ] Desde /my-orders, hacer click en "Pagar Orden"
- [ ] Verificar que se puede reintentar

### Verificaciones en Base de Datos

**Comandos Django Shell:**
```python
python manage.py shell
```

```python
from apps.orders.models import Order, Payment, PaymentTransaction
from django.utils import timezone

# Ver última orden creada
order = Order.objects.latest('created_at')
print(f"Orden: {order.id}")
print(f"Estado: {order.status.code}")
print(f"Monto: ${order.total_amount}")

# Ver payment asociado
payment = Payment.objects.filter(order=order).first()
print(f"Payment: {payment.id if payment else 'No existe'}")
print(f"Estado: {payment.status.code if payment else 'N/A'}")

# Ver transacciones
transactions = PaymentTransaction.objects.filter(order=order)
for t in transactions:
    print(f"Transaction: {t.id}")
    print(f"  Status: {t.status}")
    print(f"  Token: {t.webpay_token[:20]}..." if t.webpay_token else "  Token: None")
    print(f"  Auth Code: {t.webpay_authorization_code}")
    print(f"  Card: **** {t.card_last_four}" if t.card_last_four else "  Card: N/A")
```

### Verificar Auditoría

**En Django Admin:**
1. Ir a `http://localhost:8000/admin/audit/auditlog/`
2. Filtrar por tabla: `payment_transactions`
3. Verificar que se registran:
   - CREATE al iniciar pago
   - UPDATE al confirmar pago
4. Ver detalles de cambios en `old_values` y `new_values`

### Logs a Revisar

**Backend logs:**
```bash
# En la terminal donde corre Django
# Deberías ver:
[INFO] Creando transacción Webpay para orden 123
[INFO] Transacción creada exitosamente. Token: XXX...
[INFO] Retorno de Webpay con token: XXX...
[INFO] Confirmando transacción Webpay para token: XXX...
[INFO] Pago aprobado para orden 123
[INFO] Stock confirmado para producto 45: -2
```

**Frontend logs:**
```javascript
// En la consola del navegador (F12)
console.log('Creando orden...');
console.log('Orden creada:', order);
console.log('Iniciando pago Webpay...');
console.log('Redirigiendo a Webpay...');
console.log('Verificando pago:', { status, orderId });
```

### Troubleshooting Común

**Error: "Transacción no encontrada"**
- **Causa:** Token inválido o transacción no creada
- **Solución:** Verificar que se creó PaymentTransaction con el token

**Error: "Order already paid"**
- **Causa:** Intentar pagar orden ya pagada
- **Solución:** Validar status antes de crear transacción

**Error: "CSRF token missing"**
- **Causa:** Webpay retorna sin CSRF
- **Solución:** Ya está resuelto con `@csrf_exempt` en `webpay_return`

**No redirige a Webpay**
- **Causa:** `VITE_WEBPAY_ENABLED` no está en `true`
- **Solución:** Verificar variables de entorno en frontend

### Orden de Ejecución

1. **Iniciar servidores:**
   ```bash
   # Terminal 1: Backend
   cd condorshop/backend
   python manage.py runserver
   
   # Terminal 2: Frontend
   cd condorshop/frontend
   npm run dev
   ```

2. **Verificar configuración:**
   - Backend: `.env` tiene variables de Webpay
   - Frontend: `.env` tiene `VITE_WEBPAY_ENABLED=true`

3. **Ejecutar Test 1 (Flujo exitoso)**

4. **Verificar en base de datos**

5. **Ejecutar Test 2 (Pago rechazado)**

6. **Verificar auditoría**

7. **Ejecutar Test 3 (Usuario invitado)**

### Checklist Final de Testing

**Backend:**
- [ ] `transbank-sdk` instalado
- [ ] Variables en `.env` configuradas
- [ ] `WEBPAY_CONFIG` en `settings.py`
- [ ] Vistas de pago funcionando
- [ ] URLs de pago configuradas
- [ ] `@csrf_exempt` en `webpay_return`

**Frontend:**
- [ ] `paymentsService.js` creado
- [ ] `StepReview.jsx` modificado
- [ ] `PaymentResultPage.jsx` creado
- [ ] Ruta `/payment/result` agregada
- [ ] `VITE_WEBPAY_ENABLED=true` configurado

**Testing:**
- [ ] Pago exitoso probado
- [ ] Pago rechazado probado
- [ ] Invitado puede pagar
- [ ] Stock se decrementa correctamente
- [ ] Auditoría registra transacciones

---

## 📝 Notas Finales

Este documento consolida toda la documentación histórica relacionada con la implementación de Webpay Plus en CondorShop, incluyendo:

- Análisis completo de la arquitectura
- Documentación técnica detallada
- Soluciones a problemas encontrados
- Guías de testing y troubleshooting

**Última actualización:** Noviembre 2025  
**Mantenido por:** Equipo de desarrollo CondorShop

