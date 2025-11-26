# 🧪 INSTRUCCIONES DE TESTING - WEBPAY PLUS

## ✅ PRE-REQUISITOS VERIFICADOS

Ejecuta el script de verificación antes de comenzar:

```bash
cd condorshop/backend
python verify_webpay_setup.py
```

**Debe mostrar:** `[OK] CONFIGURACION CORRECTA`

---

## 🚀 PASO 1: INICIAR SERVIDORES

### Terminal 1: Backend Django
```bash
cd condorshop/backend
python manage.py runserver
```

**Verifica que veas:**
- `Starting development server at http://127.0.0.1:8000/`
- Sin errores de importación

### Terminal 2: Frontend React
```bash
cd condorshop/frontend
npm run dev
```

**Verifica que veas:**
- `Local: http://localhost:5173/`
- Sin errores de compilación

---

## 🧪 PASO 2: TEST 1 - FLUJO COMPLETO EXITOSO

### 2.1 Preparación
1. Abre el navegador en `http://localhost:5173`
2. Abre la consola del navegador (F12 → Console)
3. Abre la terminal del backend para ver logs

### 2.2 Ejecutar Test
1. **Agregar productos al carrito**
   - Navega a cualquier producto
   - Agrega al carrito (cantidad: 1 o 2)

2. **Ir a checkout**
   - Click en "Ver Carrito"
   - Click en "Proceder al Checkout"

3. **Completar datos**
   - **Paso 1 (Customer):** Completa nombre, email, teléfono
   - **Paso 2 (Address):** Completa dirección de envío
   - **Paso 3 (Review):** Revisa el resumen

4. **Crear orden**
   - Click en "Crear Pedido"
   - **VERIFICAR:** Debe aparecer modal "Redirigiendo a Webpay..."
   - **VERIFICAR en consola:** `Creando orden...`, `Orden creada:`, `Iniciando pago Webpay...`

5. **Redirección a Webpay**
   - **VERIFICAR:** Debe redirigir automáticamente a Webpay (URL de Transbank)
   - **VERIFICAR en backend logs:** `Creando transacción Webpay para orden X`

6. **Pagar con tarjeta de prueba**
   - **Tarjeta aprobada:** `4051 8856 0000 0002`
   - **CVV:** `123`
   - **Fecha:** Cualquier fecha futura (ej: `12/25`)
   - **RUT:** `11.111.111-1`
   - Click en "Pagar"

7. **Verificar redirección**
   - **VERIFICAR:** Debe redirigir a `/payment/result?status=success&order_id=X`
   - **VERIFICAR en frontend:** Página muestra "¡Pago Exitoso!"
   - **VERIFICAR en backend logs:** `Pago aprobado para orden X`, `Stock confirmado`

### 2.3 Verificaciones en Base de Datos

Abre Django shell:
```bash
cd condorshop/backend
python manage.py shell
```

```python
from apps.orders.models import Order, Payment, PaymentTransaction
from django.utils import timezone

# Ver última orden
order = Order.objects.latest('created_at')
print(f"Orden ID: {order.id}")
print(f"Estado: {order.status.code}")  # Debe ser 'PAID'
print(f"Monto: ${order.total_amount}")

# Ver payment
payment = Payment.objects.filter(order=order).first()
print(f"\nPayment ID: {payment.id if payment else 'No existe'}")
print(f"Estado Payment: {payment.status.code if payment else 'N/A'}")  # Debe ser 'CAPTURED'

# Ver transacción
transaction = PaymentTransaction.objects.filter(order=order).first()
print(f"\nTransaction ID: {transaction.id if transaction else 'No existe'}")
print(f"Status: {transaction.status if transaction else 'N/A'}")  # Debe ser 'approved'
print(f"Auth Code: {transaction.webpay_authorization_code if transaction else 'N/A'}")
print(f"Card: **** {transaction.card_last_four if transaction else 'N/A'}")
```

**Resultados esperados:**
- ✅ `order.status.code == 'PAID'`
- ✅ `payment.status.code == 'CAPTURED'`
- ✅ `transaction.status == 'approved'`
- ✅ `transaction.webpay_authorization_code` tiene valor
- ✅ `transaction.card_last_four` tiene valor

### 2.4 Verificar Stock

```python
from apps.products.models import Product

# Verificar que el stock se decrementó
for item in order.items.all():
    product = item.product
    print(f"\nProducto: {product.name}")
    print(f"  Stock disponible: {product.stock_available}")
    print(f"  Stock reservado: {product.stock_reserved}")
    # El stock disponible debe haber disminuido
```

---

## 🧪 PASO 3: TEST 2 - PAGO RECHAZADO

### 3.1 Ejecutar Test
1. Repite pasos 2.1 a 2.5 (crear orden y redirigir a Webpay)

2. **Usar tarjeta rechazada**
   - **Tarjeta rechazada:** `4051 8842 3993 7763`
   - **CVV:** `123`
   - **Fecha:** Cualquier fecha futura
   - **RUT:** `11.111.111-1`
   - Click en "Pagar"

3. **Verificar redirección**
   - **VERIFICAR:** Debe redirigir a `/payment/result?status=failed&message=...`
   - **VERIFICAR en frontend:** Página muestra "Pago No Completado"
   - **VERIFICAR en backend logs:** `Pago rechazado para orden X`, `Stock liberado`

### 3.2 Verificaciones en Base de Datos

```python
# Ver última orden (debe ser la rechazada)
order = Order.objects.latest('created_at')
print(f"Orden ID: {order.id}")
print(f"Estado: {order.status.code}")  # Debe ser 'FAILED'

payment = Payment.objects.filter(order=order).first()
print(f"Estado Payment: {payment.status.code if payment else 'N/A'}")  # Debe ser 'FAILED'

transaction = PaymentTransaction.objects.filter(order=order).first()
print(f"Status Transaction: {transaction.status if transaction else 'N/A'}")  # Debe ser 'rejected'
```

**Resultados esperados:**
- ✅ `order.status.code == 'FAILED'`
- ✅ `payment.status.code == 'FAILED'`
- ✅ `transaction.status == 'rejected'`
- ✅ Stock NO debe haberse decrementado (se liberó)

---

## 🧪 PASO 4: TEST 3 - USUARIO INVITADO

### 4.1 Ejecutar Test
1. **Cerrar sesión** (si estás logueado)
2. Repite pasos 2.1 a 2.7 (todo el flujo sin autenticación)

**VERIFICAR:**
- ✅ Puede agregar productos al carrito (usa session_token)
- ✅ Puede completar checkout como invitado
- ✅ Puede pagar con Webpay
- ✅ La orden se crea correctamente (order.user puede ser NULL)

---

## 📊 PASO 5: VERIFICAR AUDITORÍA

### 5.1 En Django Admin
1. Ir a `http://localhost:8000/admin/audit/auditlog/`
2. Filtrar por tabla: `payment_transactions`
3. **VERIFICAR:**
   - ✅ Se registra `CREATE` al iniciar pago
   - ✅ Se registra `UPDATE` al confirmar pago
   - ✅ `old_values` y `new_values` muestran los cambios

### 5.2 Verificar en Shell

```python
from apps.audit.models import AuditLog

# Ver últimos registros de payment_transactions
logs = AuditLog.objects.filter(table_name='payment_transactions').order_by('-created_at')[:5]
for log in logs:
    print(f"\n{log.created_at} - {log.action}")
    print(f"  Tabla: {log.table_name}")
    print(f"  Record ID: {log.record_id}")
    if log.new_values:
        print(f"  Nuevos valores: {log.new_values}")
```

---

## 📝 LOGS A REVISAR

### Backend (Terminal donde corre Django)
**Logs esperados durante pago exitoso:**
```
[INFO] Creando transacción Webpay para orden 123
[INFO] Transacción creada exitosamente. Token: XXX...
[INFO] PaymentTransaction 456 creada para orden 123
[INFO] Retorno de Webpay con token: XXX...
[INFO] Confirmando transacción Webpay para token: XXX...
[INFO] Respuesta Webpay: {...}
[INFO] Pago aprobado para orden 123
[INFO] Stock confirmado para producto 45: -2
[INFO] Redirigiendo a: http://localhost:5173/payment/result?status=success&order_id=123
```

### Frontend (Consola del navegador - F12)
**Logs esperados:**
```javascript
Creando orden...
Orden creada: {id: 123, ...}
Iniciando pago Webpay para orden: 123
Respuesta de Webpay: {success: true, token: "...", url: "..."}
Redirigiendo a Webpay...
Verificando pago: {status: "success", orderId: "123"}
Estado de pago: {order_id: 123, order_status: "PAID", ...}
```

---

## 🚨 TROUBLESHOOTING

### Error: "Webpay no está disponible"
**Causa:** `transbank-sdk` no instalado
**Solución:**
```bash
cd condorshop/backend
pip install transbank-sdk==3.0.0
```

### Error: "No redirige a Webpay"
**Causa:** `VITE_WEBPAY_ENABLED` no está en `true`
**Solución:**
1. Verificar `frontend/.env` tiene `VITE_WEBPAY_ENABLED=true`
2. Reiniciar servidor frontend (`npm run dev`)

### Error: "CSRF token missing" en webpay_return
**Causa:** Ya está resuelto con `@csrf_exempt`
**Si persiste:** Verificar que `@csrf_exempt` esté en `webpay_return`

### Error: "Transacción no encontrada"
**Causa:** Token inválido o transacción no creada
**Solución:** Verificar en base de datos que existe `PaymentTransaction` con el token

### Error: "Order already paid"
**Causa:** Intentar pagar orden ya pagada
**Solución:** Crear una nueva orden para probar

---

## ✅ CHECKLIST FINAL DE TESTING

### Backend
- [ ] `transbank-sdk` instalado y funcionando
- [ ] Variables en `.env` configuradas correctamente
- [ ] `WEBPAY_CONFIG` en `settings.py` correcto
- [ ] Vistas de pago responden correctamente
- [ ] URLs de pago configuradas
- [ ] `@csrf_exempt` en `webpay_return` funciona

### Frontend
- [ ] `paymentsService.js` funciona
- [ ] `StepReview.jsx` redirige a Webpay
- [ ] `PaymentResultPage.jsx` muestra resultados correctos
- [ ] Ruta `/payment/result` funciona
- [ ] `VITE_WEBPAY_ENABLED=true` configurado

### Testing
- [ ] Test 1: Pago exitoso completado
- [ ] Test 2: Pago rechazado completado
- [ ] Test 3: Usuario invitado puede pagar
- [ ] Stock se decrementa correctamente (pago exitoso)
- [ ] Stock se libera correctamente (pago rechazado)
- [ ] Auditoría registra todas las transacciones
- [ ] Estados de orden se actualizan correctamente

---

## 🎉 SIGUIENTE PASO: PRODUCCIÓN

Una vez que todos los tests pasen:

1. **Obtener credenciales de producción** de Transbank
2. **Actualizar `.env` del backend:**
   ```bash
   WEBPAY_ENVIRONMENT=production
   WEBPAY_COMMERCE_CODE=<tu_codigo_real>
   WEBPAY_API_KEY=<tu_api_key_real>
   WEBPAY_RETURN_URL=https://condorshop.cl/api/payments/return/
   WEBPAY_FINAL_URL=https://condorshop.cl/payment/result
   ```
3. **Configurar certificados SSL** en tu servidor
4. **Probar en producción** con tarjetas reales (monto mínimo)
5. **Monitorear logs** de producción

---

**¿Listo para probar? Sigue los pasos en orden y reporta cualquier problema encontrado.**


