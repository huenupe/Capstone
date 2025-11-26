"""Servicios y utilidades para el dominio de pedidos."""

import logging
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.products.models import Product

from .models import ShippingRule, ShippingZone, ShippingCarrier, Order, OrderStatus, Payment, PaymentStatus, PaymentTransaction

logger = logging.getLogger(__name__)


DEFAULT_FREE_SHIPPING_THRESHOLD = 50000
DEFAULT_SHIPPING_COST = 5000


def _to_int(value) -> int:
    """Convertir un valor numérico (o string) a entero CLP con redondeo half-up."""
    if isinstance(value, int):
        return value
    if value is None:
        return 0
    value_str = str(value)
    if not value_str:
        return 0
    if '.' not in value_str:
        return int(value_str)
    integer_part, fractional_part = value_str.split('.', 1)
    fractional_part = (fractional_part + '00')[:2]
    rounded = int(integer_part or '0')
    if int(fractional_part) >= 50:
        rounded += 1
    return rounded


def _extract_product_context(cart_items: Sequence) -> tuple[list[int], Set[int]]:
    """Obtener IDs de productos y categorías desde los items del carrito."""
    product_ids: list[int] = []
    category_ids: Set[int] = set()
    missing_product_ids: Set[int] = set()

    for item in cart_items:
        product = getattr(item, "product", None)

        if isinstance(item, dict):
            product_id = item.get("product_id")
        else:
            product_id = getattr(item, "product_id", None)

        if not product_id:
            continue

        product_ids.append(product_id)

        if product and getattr(product, "category_id", None):
            category_ids.add(product.category_id)
        else:
            missing_product_ids.add(product_id)

    if missing_product_ids:
        for product in Product.objects.filter(id__in=missing_product_ids).select_related("category"):
            if product.category_id:
                category_ids.add(product.category_id)

    return product_ids, category_ids


def _calculate_total_weight(cart_items: Optional[Iterable]) -> float:
    """Calcula el peso total de los items del carrito en kg"""
    if not cart_items:
        return 0.0
    
    total_weight = 0.0
    for item in cart_items:
        product = getattr(item, "product", None)
        
        if isinstance(item, dict):
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
        else:
            product_id = getattr(item, "product_id", None)
            quantity = getattr(item, "quantity", 1)
        
        if not product_id:
            continue
        
        if not product:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
        
        weight = float(product.weight or 0)
        total_weight += weight * quantity
    
    return total_weight


def evaluate_shipping(region: Optional[str], subtotal, cart_items: Optional[Iterable]) -> dict:
    """
    Determinar costo de envío y metadatos relevantes reutilizables en el checkout.
    Usa la nueva estructura de ShippingRule con carrier, peso y criterios múltiples.

    Retorna un diccionario con las llaves:
    - cost (int)
    - free_shipping_threshold (int | None)
    - zone (str | None)
    - carrier (str | None)
    - applied_rule_id (int | None)
    """

    subtotal_int = _to_int(subtotal)
    total_weight = _calculate_total_weight(cart_items)

    if not region or not cart_items:
        cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
        return {
            "cost": cost,
            "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
            "zone": None,
            "carrier": None,
            "applied_rule_id": None,
        }

    # Resolver zona
    zone = ShippingZone.objects.filter(
        is_active=True,
        regions__icontains=region,
    ).first()

    # Obtener reglas activas ordenadas por prioridad
    rules_qs = ShippingRule.objects.filter(
        is_active=True,
        carrier__is_active=True
    ).select_related('carrier', 'zone').order_by('-priority', 'base_cost')

    # Filtrar por zona si existe
    if zone:
        rules_qs = rules_qs.filter(zone__in=[zone, None])
    else:
        rules_qs = rules_qs.filter(zone__isnull=True)

    # Buscar la primera regla que aplique
    applied_rule = None
    for rule in rules_qs:
        if rule.applies_to(zone, subtotal_int, total_weight):
            applied_rule = rule
            break

    if applied_rule:
        cost = applied_rule.calculate_cost(subtotal_int, total_weight)
        return {
            "cost": cost,
            "free_shipping_threshold": applied_rule.free_shipping_threshold,
            "zone": zone.name if zone else None,
            "carrier": applied_rule.carrier.name if applied_rule.carrier else None,
            "applied_rule_id": applied_rule.id,
        }

    # Fallback por defecto
    cost = 0 if subtotal_int >= DEFAULT_FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_COST
    return {
        "cost": cost,
        "free_shipping_threshold": DEFAULT_FREE_SHIPPING_THRESHOLD,
        "zone": zone.name if zone else None,
        "carrier": None,
        "applied_rule_id": None,
    }


def send_order_confirmation_email(order):
    """
    Envía email de confirmación de pedido al cliente.
    
    Args:
        order: Orden confirmada (Order)
    
    Returns:
        bool: True si el email se envió exitosamente, False en caso de error
    """
    # Obtener datos del cliente desde shipping_snapshot
    customer_name = ''
    customer_email = ''
    if order.shipping_snapshot:
        customer_name = order.shipping_snapshot.customer_name or ''
        customer_email = order.shipping_snapshot.customer_email or ''
    
    # Validar que hay email del cliente
    if not customer_email:
        logger.warning(f"No se puede enviar email de confirmación para pedido #{order.id}: email del cliente no disponible")
        return False
    
    subject = f'Confirmación de pedido #{order.id} - CondorShop'
    message = f"""Hola {customer_name},

Tu pedido #{order.id} ha sido confirmado.

Total: ${order.total_amount:,.0f} CLP
Estado: {order.status.description}

Gracias por tu compra!

CondorShop
"""

    # Enviar email de confirmación
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        logger.info(f"Email de confirmación enviado para pedido #{order.id} a {customer_email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email de confirmación para pedido #{order.id}: {str(e)}")
        return False


# ============================================
# WEBPAY PLUS SERVICE
# ============================================

# Importación lazy - se importará cuando se necesite
# Si no está instalado, fallará con error claro al intentar usar Webpay
_transbank_available = None
_transbank_error = None

def _check_transbank():
    """Verifica si transbank-sdk está disponible. Retorna (disponible, error)"""
    global _transbank_available, _transbank_error
    
    if _transbank_available is not None:
        return _transbank_available, _transbank_error
    
    try:
        from transbank.error.transbank_error import TransbankError
        from transbank.webpay.webpay_plus.transaction import Transaction
        _transbank_available = True
        _transbank_error = None
        return True, None
    except ImportError as e:
        _transbank_available = False
        _transbank_error = e
        return False, e

def _get_transbank_imports():
    """Obtiene las importaciones de transbank. Falla con error claro si no está disponible."""
    available, error = _check_transbank()
    if not available:
        raise ImportError(
            f"transbank-sdk no está instalado. "
            f"Error original: {error}. "
            f"Instala con: pip install transbank-sdk==3.0.0"
        )
    from transbank.error.transbank_error import TransbankError
    from transbank.webpay.webpay_plus.transaction import Transaction
    return TransbankError, Transaction


class WebpayService:
    """Servicio para manejar transacciones de Webpay Plus"""

    def __init__(self):
        """Inicializa el servicio con la configuración de Transbank"""
        # Verificar que transbank esté disponible - fallará con error claro si no lo está
        TransbankError, Transaction = _get_transbank_imports()
        
        self.config = settings.WEBPAY_CONFIG
        self.environment = self.config['ENVIRONMENT']

        # Validación de credenciales para integración
        if self.environment == 'integration':
            expected_commerce_code = '597055555532'
            expected_api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
            
            if self.config['COMMERCE_CODE'] != expected_commerce_code:
                logger.warning(
                    f"Commerce Code incorrecto para integración. "
                    f"Esperado: {expected_commerce_code}, "
                    f"Actual: {self.config['COMMERCE_CODE']}"
                )
            
            if self.config['API_KEY'] != expected_api_key:
                logger.warning(
                    f"API Key incorrecto para integración. "
                    f"Verifica tu archivo .env"
                )

        # Configurar SDK según ambiente
        if self.environment == 'production':
            Transaction.commerce_code = self.config['COMMERCE_CODE']
            Transaction.api_key = self.config['API_KEY']
            logger.info(f"Webpay configurado para PRODUCCIÓN - Commerce Code: {self.config['COMMERCE_CODE']}")
        else:
            logger.info("Webpay configurado para INTEGRACIÓN (testing)")
        
        logger.info(f"WebpayService inicializado - Ambiente: {self.environment}")

    def create_transaction(self, order: Order) -> Tuple[bool, str, Optional[Dict]]:
        """
        Crea una transacción de pago en Webpay

        Args:
            order: Orden a pagar

        Returns:
            Tuple[success, token_or_error, response_data]
        """
        try:
            # Validar que la orden no esté ya pagada
            if order.status.code in ['PAID', 'PREPARING', 'SHIPPED', 'DELIVERED']:
                logger.warning(f"Intento de pagar orden ya pagada: {order.id}")
                return False, "La orden ya ha sido pagada", None

            # Validar que no haya transacción pendiente
            # Usar SQL raw para evitar deserializar gateway_response que puede tener datos corruptos
            existing_transaction_token = None
            try:
                # Leer solo webpay_token usando SQL raw para evitar deserialización de JSONField
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT webpay_token, webpay_buy_order
                        FROM payment_transactions 
                        WHERE order_id = %s AND status = 'pending' AND webpay_token IS NOT NULL
                        LIMIT 1
                    """, [order.id])
                    row = cursor.fetchone()
                    if row:
                        existing_transaction_token = row[0]
                        existing_buy_order = row[1] if len(row) > 1 else None
                        logger.info(f"[WEBPAY] Transacción pendiente encontrada - Token: {existing_transaction_token[:20]}..., Buy Order: {existing_buy_order}")
            except Exception as e:
                logger.error(f"[WEBPAY] ERROR al leer transacción existente: {type(e).__name__}: {str(e)}")
                logger.error(f"[WEBPAY] Traceback:", exc_info=True)
                logger.warning(f"[WEBPAY] Continuando con creación de nueva transacción para orden {order.id}")
                existing_transaction_token = None

            if existing_transaction_token:
                logger.info(f"[WEBPAY] Reutilizando token existente para orden {order.id}")
                # Usar URL por defecto de Webpay (no intentamos leer gateway_response corrupto)
                url = 'https://webpay3gint.transbank.cl/webpayserver/initTransaction'
                
                return True, existing_transaction_token, {
                    'token': existing_transaction_token,
                    'url': url
                }
            
            # Validar monto de la orden
            if not order.total_amount or order.total_amount <= 0:
                logger.error(f"[WEBPAY] Orden {order.id} tiene monto inválido: {order.total_amount}")
                return False, "El monto de la orden debe ser mayor a 0", None
            
            # Convertir monto a entero (pesos chilenos sin decimales)
            try:
                amount = int(order.total_amount)
            except (ValueError, TypeError) as e:
                logger.error(f"[WEBPAY] No se puede convertir monto a entero: {order.total_amount} - {e}")
                return False, "El monto de la orden tiene un formato inválido", None
            
            # Validar rango de monto (Webpay tiene límites)
            if amount < 50:  # Monto mínimo
                logger.error(f"[WEBPAY] Monto muy bajo: {amount}")
                return False, "El monto mínimo es de $50 CLP", None
            
            if amount > 999999999:  # Monto máximo de Webpay
                logger.error(f"[WEBPAY] Monto muy alto: {amount}")
                return False, "El monto excede el límite permitido", None

            # Generar buy_order único (máximo 26 caracteres según validación de Transbank SDK)
            # Formato optimizado: {order_id}-{timestamp_compacto}
            # Usar microsegundos para evitar colisiones en el mismo segundo
            from datetime import timedelta
            now = timezone.now()
            # Formato compacto: YYMMDDHHMMSS + últimos 3 dígitos de microsegundos
            # Esto nos da 12 dígitos de timestamp + hasta 10 caracteres para "ORDER-{id}-" = 22 caracteres máximo
            timestamp_compact = now.strftime('%y%m%d%H%M%S') + str(now.microsecond)[-3:]  # Últimos 3 dígitos de microsegundos
            # Formato: ORDER-{order_id}-{timestamp_compact}
            # Ejemplo: ORDER-1-251118234517454 (26 caracteres máximo)
            buy_order = f"ORD-{order.id}-{timestamp_compact}"
            
            # Asegurar que no exceda 26 caracteres (límite real de Transbank)
            if len(buy_order) > 26:
                # Si excede, truncar timestamp pero mantener unicidad
                max_timestamp_length = 26 - len(f"ORD-{order.id}-")
                if max_timestamp_length > 0:
                    timestamp_compact = timestamp_compact[:max_timestamp_length]
                    buy_order = f"ORD-{order.id}-{timestamp_compact}"
                else:
                    # Si order_id es muy grande, usar formato más corto
                    buy_order = f"O{order.id}-{timestamp_compact[:15]}"
                    if len(buy_order) > 26:
                        buy_order = buy_order[:26]
            
            # Verificar si hay buy_orders duplicados y generar contador si es necesario
            logger.info(f"[WEBPAY] Verificando buy_orders duplicados antes de crear...")
            duplicate_counter = 0
            max_attempts = 10  # Límite de intentos para evitar loop infinito
            
            for attempt in range(max_attempts):
                try:
                    from django.db import connection
                    # Verificar si el buy_order ya existe
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM payment_transactions 
                            WHERE webpay_buy_order = %s
                        """, [buy_order])
                        count = cursor.fetchone()[0]
                        
                        if count == 0:
                            # buy_order único encontrado
                            logger.info(f"[WEBPAY] buy_order único generado: '{buy_order}'")
                            break
                        else:
                            # Duplicado encontrado, generar nuevo con contador
                            duplicate_counter += 1
                            logger.warning(
                                f"[WEBPAY] ADVERTENCIA: buy_order duplicado encontrado: '{buy_order}' "
                                f"(intento {attempt + 1}/{max_attempts})"
                            )
                            # Agregar contador al final (respetando límite de 26 caracteres)
                            buy_order = f"ORD-{order.id}-{timestamp_compact}-{duplicate_counter}"
                            
                            if len(buy_order) > 26:
                                # Si excede 26 caracteres, truncar timestamp pero mantener contador
                                max_base_length = 26 - len(str(duplicate_counter)) - 1  # -1 para el guión
                                base = f"ORD-{order.id}-"
                                remaining = max_base_length - len(base)
                                if remaining > 0:
                                    truncated_timestamp = timestamp_compact[:remaining]
                                    buy_order = f"{base}{truncated_timestamp}-{duplicate_counter}"
                                else:
                                    # Si aún es muy largo, usar formato más corto
                                    buy_order = f"O{order.id}-{timestamp_compact[:10]}-{duplicate_counter}"
                                    if len(buy_order) > 26:
                                        buy_order = buy_order[:26]
                                logger.warning(f"[WEBPAY] buy_order truncado por longitud: '{buy_order}'")
                            
                            if attempt == max_attempts - 1:
                                # Último intento falló
                                error_msg = f"No se pudo generar buy_order único después de {max_attempts} intentos"
                                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                                return False, error_msg, None
                except Exception as e:
                    logger.error(f"[WEBPAY] ERROR al verificar buy_orders duplicados: {type(e).__name__}: {str(e)}")
                    logger.error(f"[WEBPAY] Traceback:", exc_info=True)
                    # Continuar con el buy_order generado - el índice único en BD lo protegerá
                    break
            
            # Asegurar que no exceda 26 caracteres (límite real de Transbank - verificación final)
            if len(buy_order) > 26:
                buy_order = buy_order[:26]
                logger.warning(f"[WEBPAY] buy_order truncado a 26 caracteres: '{buy_order}'")
            
            if duplicate_counter > 0:
                logger.info(f"[WEBPAY] buy_order generado con contador después de {duplicate_counter} duplicados encontrados")
            
            # Session ID (máximo 64 caracteres)
            session_id = f"SESSION-{order.id}"
            if len(session_id) > 64:
                session_id = session_id[:64]
                logger.warning(f"[WEBPAY] session_id truncado a 64 caracteres: {session_id}")
            
            return_url = self.config['RETURN_URL']
            
            logger.info(f"[WEBPAY] Parámetros generados:")
            logger.info(f"[WEBPAY]   - buy_order final: '{buy_order}' ({len(buy_order)} caracteres)")
            logger.info(f"[WEBPAY]   - session_id final: '{session_id}' ({len(session_id)} caracteres)")
            logger.info(f"[WEBPAY]   - return_url: '{return_url}'")

            # Crear transacción en Webpay
            logger.info(f"[WEBPAY] Creando transacción para orden {order.id}")
            logger.debug(f"[WEBPAY] Buy Order: {buy_order}, Amount: {amount}, Return URL: {return_url}")

            # CRÍTICO: Re-importar Transaction para uso directo
            _, Transaction = _get_transbank_imports()
            logger.debug(f"[WEBPAY] Transaction clase importada: {Transaction}")
            
            # CREAR INSTANCIA de Transaction
            transaction = Transaction()
            logger.debug(f"[WEBPAY] Instancia de Transaction creada: {transaction}")
            
            # Configurar la INSTANCIA para el ambiente
            if self.environment == 'production':
                transaction.commerce_code = self.config['COMMERCE_CODE']
                transaction.api_key = self.config['API_KEY']
                logger.debug(f"[WEBPAY] Instancia configurada para PRODUCCIÓN")
            else:
                logger.debug(f"[WEBPAY] Instancia usa credenciales de INTEGRACIÓN por defecto")
            
            logger.info(f"[WEBPAY] Llamando a transaction.create() en la instancia...")
            logger.debug(f"[WEBPAY] Buy Order: {buy_order}")
            logger.debug(f"[WEBPAY] Session ID: {session_id}")
            logger.debug(f"[WEBPAY] Amount: {amount}")
            logger.debug(f"[WEBPAY] Return URL: {return_url}")
            
            # Validar parámetros antes de enviar
            logger.info(f"[WEBPAY] Validando parámetros antes de crear transacción:")
            logger.info(f"[WEBPAY]   - buy_order: '{buy_order}' (tipo: {type(buy_order).__name__}, longitud: {len(buy_order)})")
            logger.info(f"[WEBPAY]   - session_id: '{session_id}' (tipo: {type(session_id).__name__}, longitud: {len(session_id)})")
            logger.info(f"[WEBPAY]   - amount: {amount} (tipo: {type(amount).__name__})")
            logger.info(f"[WEBPAY]   - return_url: '{return_url}' (tipo: {type(return_url).__name__})")
            
            # Validaciones adicionales
            if not buy_order or len(buy_order) > 26:
                error_msg = f"buy_order inválido: '{buy_order}' (debe tener máximo 26 caracteres según Transbank)"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                return False, error_msg, None
            
            if not session_id or len(session_id) > 64:
                error_msg = f"session_id inválido: '{session_id}' (debe tener máximo 64 caracteres)"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                return False, error_msg, None
            
            if not isinstance(amount, int) or amount <= 0:
                error_msg = f"amount inválido: {amount} (debe ser un entero positivo)"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                return False, error_msg, None
            
            if not return_url or not return_url.startswith(('http://', 'https://')):
                error_msg = f"return_url inválido: '{return_url}' (debe ser una URL válida)"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                return False, error_msg, None
            
            logger.info(f"[WEBPAY] Todos los parámetros son válidos. Llamando a transaction.create()...")
            
            try:
                response = transaction.create(
                    buy_order=buy_order,
                    session_id=session_id,
                    amount=amount,
                    return_url=return_url
                )
                logger.info(f"[WEBPAY] transaction.create() ejecutado sin excepciones")
            except Exception as create_error:
                logger.error(f"[WEBPAY] ERROR AL LLAMAR transaction.create():")
                logger.error(f"[WEBPAY] Tipo de error: {type(create_error).__name__}")
                logger.error(f"[WEBPAY] Mensaje: {str(create_error)}")
                logger.error(f"[WEBPAY] Traceback completo:", exc_info=True)
                # Re-lanzar el error para que sea manejado por el bloque except externo
                raise
            
            logger.info(f"[WEBPAY] Respuesta recibida de Webpay")
            logger.info(f"[WEBPAY] Tipo de respuesta: {type(response).__name__}")
            logger.info(f"[WEBPAY] Contenido completo de respuesta: {response}")
            
            # Validar que la respuesta sea un diccionario
            if not isinstance(response, dict):
                error_msg = f"La respuesta de Webpay no es un diccionario: {type(response).__name__}"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                logger.error(f"[WEBPAY] Respuesta recibida: {response}")
                return False, error_msg, None
            
            # Validar que la respuesta tenga los campos necesarios
            token = response.get('token')
            url = response.get('url')
            
            logger.info(f"[WEBPAY] Token extraído: {token[:20] + '...' if token and len(token) > 20 else token}")
            logger.info(f"[WEBPAY] URL extraída: {url}")
            
            if not token:
                error_msg = "La respuesta de Webpay no contiene token"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                logger.error(f"[WEBPAY] Respuesta completa: {response}")
                return False, error_msg, None
            
            if not url:
                error_msg = "La respuesta de Webpay no contiene URL"
                logger.error(f"[WEBPAY] ERROR: {error_msg}")
                logger.error(f"[WEBPAY] Respuesta completa: {response}")
                return False, error_msg, None
            
            logger.info(f"[WEBPAY] Respuesta validada correctamente")

            # Crear o actualizar Payment
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method': 'webpay',
                    'status': PaymentStatus.objects.get(code='CREATED'),
                    'currency': 'CLP'
                }
            )

            if not created:
                logger.info(f"[WEBPAY] Payment {payment.id} ya existía para orden {order.id}")

            # ✅ CORRECCIÓN: Serializar gateway_response como JSON string antes de guardar
            import json
            gateway_response_data = {
                'token': response['token'],
                'url': response['url'],
                'created_at': timezone.now().isoformat(),
                'environment': self.environment
            }
            # Asegurar que se guarde como JSON string válido
            gateway_response_json = json.dumps(gateway_response_data, default=str)
            
            # Crear PaymentTransaction
            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='webpay',
                status='pending',
                amount=amount,
                webpay_token=response['token'],
                webpay_buy_order=buy_order,
                gateway_response=json.loads(gateway_response_json)  # Django JSONField lo serializará correctamente
            )

            logger.info(f"[WEBPAY] PaymentTransaction creada exitosamente: ID={transaction.id}")

            return True, response['token'], {
                'token': response['token'],
                'url': response['url'],
                'buy_order': buy_order,
                'transaction_id': transaction.id
            }

        except ImportError as e:
            logger.error(f"[WEBPAY] ERROR: Error de importación: {str(e)}", exc_info=True)
            return False, f"Error de configuración: transbank-sdk no disponible", None
        
        except AttributeError as e:
            logger.error(f"[WEBPAY] ERROR: Error de atributo: {str(e)}", exc_info=True)
            return False, f"Error de configuración: método create no encontrado", None
        
        except Exception as e:
            logger.error(f"[WEBPAY] ERROR: Error al crear transacción: {str(e)}", exc_info=True)
            
            # Verificar si es un error de Transbank
            try:
                TransbankError, _ = _get_transbank_imports()
                if isinstance(e, TransbankError):
                    logger.error(f"[WEBPAY] ERROR TRANSBANK DETECTADO: {type(e).__name__}")
                    logger.error(f"[WEBPAY] Mensaje de error: {str(e)}")
                    logger.error(f"[WEBPAY] Detalles completos del error:", exc_info=True)
                    # Intentar obtener más detalles del error si están disponibles
                    if hasattr(e, 'message'):
                        logger.error(f"[WEBPAY] Error.message: {e.message}")
                    if hasattr(e, 'code'):
                        logger.error(f"[WEBPAY] Error.code: {e.code}")
                    return False, f"Error de Transbank: {str(e)}", None
            except ImportError as import_err:
                # NO silenciar - registrar el error de importación también
                logger.error(f"[WEBPAY] ERROR: No se pudo importar TransbankError para verificar tipo de error")
                logger.error(f"[WEBPAY] Error de importación: {str(import_err)}", exc_info=True)
            
            # Determinar tipo de error
            error_type = type(e).__name__
            error_message = str(e)
            
            if 'TransbankError' in error_type:
                return False, f"Error de Transbank: {error_message}", None
            elif 'IntegrityError' in error_type:
                return False, f"Error de base de datos: {error_message}", None
            else:
                return False, f"Error interno: {error_message}", None

    def _update_gateway_response(self, transaction_id: int, updates: dict):
        """
        Helper para actualizar gateway_response usando raw SQL.
        Evita el error de deserialización cuando PostgreSQL devuelve JSONB como dict.
        
        Args:
            transaction_id: ID de la transacción
            updates: Dict con los campos a actualizar/agregar
        
        Raises:
            Exception: Si la transacción no existe o hay error en la actualización
        """
        from django.db import connection
        import json
        
        try:
            # Leer gateway_response actual usando raw SQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT gateway_response
                    FROM payment_transactions
                    WHERE id = %s
                """, [transaction_id])
                row = cursor.fetchone()
                
                if not row:
                    error_msg = f"Transacción {transaction_id} no encontrada al actualizar gateway_response"
                    logger.error(f"[WEBPAY] {error_msg}")
                    raise PaymentTransaction.DoesNotExist(error_msg)
                
                current_response = {}
                if row[0]:
                    # Si es un dict (PostgreSQL JSONB), usarlo directamente
                    if isinstance(row[0], dict):
                        current_response = row[0]
                    # Si es un string JSON, parsearlo
                    elif isinstance(row[0], str):
                        try:
                            current_response = json.loads(row[0])
                        except (json.JSONDecodeError, TypeError) as parse_err:
                            # NO silenciar - registrar el error pero continuar con dict vacío
                            logger.warning(
                                f"[WEBPAY] No se pudo parsear gateway_response (ID {transaction_id}) como JSON: {str(parse_err)}"
                            )
                            logger.debug(f"[WEBPAY] Contenido que falló: {str(row[0])[:200]}")
                            current_response = {}
                
                # Actualizar con los nuevos valores
                current_response.update(updates)
                
                # Guardar como JSON string
                gateway_response_json = json.dumps(current_response, default=str)
                
                # Actualizar usando raw SQL
                cursor.execute("""
                    UPDATE payment_transactions
                    SET gateway_response = %s::jsonb
                    WHERE id = %s
                """, [gateway_response_json, transaction_id])
                
                logger.debug(f"[WEBPAY] gateway_response actualizado para transacción {transaction_id}")
                
        except Exception as e:
            # NO silenciar - registrar y re-lanzar el error
            logger.error(
                f"[WEBPAY] ERROR al actualizar gateway_response para transacción {transaction_id}: {type(e).__name__}: {str(e)}"
            )
            logger.error(f"[WEBPAY] Traceback:", exc_info=True)
            raise

    def confirm_transaction(self, token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Confirma una transacción de Webpay y actualiza la orden

        Args:
            token: Token de la transacción

        Returns:
            Tuple[success, message, response_data]
        """
        db_transaction = None
        try:
            # ✅ CORRECCIÓN: Usar raw SQL para leer la transacción sin deserializar gateway_response
            # PostgreSQL devuelve JSONB como dict, y Django intenta hacer json.loads() sobre él, causando el error
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, order_id, status, amount, webpay_buy_order, webpay_token
                    FROM payment_transactions
                    WHERE webpay_token = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, [token])
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"Transacción no encontrada para token: {token[:20]}...")
                    return False, "Transacción no encontrada", None
                
                # Obtener la transacción usando solo el ID (sin cargar gateway_response)
                transaction_id = row[0]
                order_id = row[1]
                transaction_status = row[2]
                transaction_amount = row[3]
                buy_order = row[4]
                webpay_token_db = row[5]
            
            # Cargar la transacción sin gateway_response usando only()
            db_transaction = PaymentTransaction.objects.only(
                'id', 'order_id', 'status', 'amount', 'webpay_buy_order', 
                'webpay_token', 'payment_method', 'currency'
            ).select_related('order', 'order__status').get(id=transaction_id)

            order = db_transaction.order

            # Validar que no esté ya procesada
            if db_transaction.status in ['approved', 'rejected']:
                logger.warning(f"Transacción {db_transaction.id} ya procesada: {db_transaction.status}")
                return db_transaction.status == 'approved', "Transacción ya procesada", {
                    'order_id': order.id,
                    'status': db_transaction.status
                }

            # Confirmar en Webpay
            logger.info(f"[WEBPAY] Confirmando transacción para token: {token[:20]}...")
            # Re-importar Transaction para uso directo
            _, Transaction = _get_transbank_imports()
            
            # CREAR INSTANCIA de Transaction
            transaction = Transaction()
            
            # Configurar la INSTANCIA
            if self.environment == 'production':
                transaction.commerce_code = self.config['COMMERCE_CODE']
                transaction.api_key = self.config['API_KEY']
            
            # Llamar commit() en la INSTANCIA
            response = transaction.commit(token=token)
            logger.info(f"[WEBPAY] Respuesta de commit recibida exitosamente")
            logger.debug(f"[WEBPAY] Tipo de respuesta: {type(response)}")

            # ✅ CORRECCIÓN: Convertir response a un dict serializable
            # El SDK puede devolver objetos custom que no son JSON-serializables
            import json
            try:
                # Intentar serializar y deserializar para limpiar objetos no serializables
                response_clean = json.loads(json.dumps(response, default=str))
            except (TypeError, ValueError) as e:
                logger.warning(f"[WEBPAY] No se pudo limpiar response, usando dict directo: {e}")
                # Fallback: extraer solo los campos que necesitamos
                response_clean = {
                    'response_code': response.get('response_code'),
                    'amount': response.get('amount'),
                    'buy_order': response.get('buy_order'),
                    'authorization_code': response.get('authorization_code'),
                    'transaction_date': response.get('transaction_date'),
                    'card_detail': response.get('card_detail', {}),
                    'vci': response.get('vci'),
                    'session_id': response.get('session_id'),
                }
            
            logger.debug(f"[WEBPAY] Response limpio: {response_clean}")

            # VALIDACIÓN CRÍTICA: Verificar que los valores coincidan con los originales
            response_amount = response.get('amount')
            response_buy_order = response.get('buy_order')
            
            # Validar monto (crítico para seguridad)
            if response_amount is not None and response_amount != db_transaction.amount:
                logger.error(
                    f"[WEBPAY] ERROR CRÍTICO: Monto no coincide. "
                    f"Esperado: {db_transaction.amount}, Recibido: {response_amount}"
                )
                db_transaction.status = 'failed'
                db_transaction.save(update_fields=['status'])
                # Actualizar gateway_response usando raw SQL
                try:
                    self._update_gateway_response(db_transaction.id, {
                        'commit_response': response_clean,
                        'committed_at': timezone.now().isoformat(),
                        'validation_error': 'Monto no coincide',
                        'expected_amount': db_transaction.amount,
                        'received_amount': response_amount
                    })
                except Exception as update_err:
                    # NO silenciar - registrar el error pero continuar
                    logger.error(
                        f"[WEBPAY] ERROR al actualizar gateway_response después de validación de monto: {type(update_err).__name__}: {str(update_err)}"
                    )
                return False, "Error de validación: el monto de la transacción no coincide", None

            # Validar buy_order (crítico para seguridad)
            if response_buy_order and response_buy_order != db_transaction.webpay_buy_order:
                logger.error(
                    f"[WEBPAY] ERROR CRÍTICO: Buy Order no coincide. "
                    f"Esperado: {db_transaction.webpay_buy_order}, Recibido: {response_buy_order}"
                )
                db_transaction.status = 'failed'
                db_transaction.save(update_fields=['status'])
                # Actualizar gateway_response usando raw SQL
                try:
                    self._update_gateway_response(db_transaction.id, {
                        'commit_response': response_clean,
                        'committed_at': timezone.now().isoformat(),
                        'validation_error': 'Buy Order no coincide',
                        'expected_buy_order': db_transaction.webpay_buy_order,
                        'received_buy_order': response_buy_order
                    })
                except Exception as update_err:
                    # NO silenciar - registrar el error pero continuar
                    logger.error(
                        f"[WEBPAY] ERROR al actualizar gateway_response después de validación de buy_order: {type(update_err).__name__}: {str(update_err)}"
                    )
                return False, "Error de validación: la orden de compra no coincide", None

            logger.info(f"[WEBPAY] Validación exitosa: monto y buy_order coinciden con valores originales")

            # ✅ Actualizar transacción con respuesta LIMPIA usando raw SQL
            try:
                self._update_gateway_response(db_transaction.id, {
                    'commit_response': response_clean,  # ← Usar response_clean
                    'committed_at': timezone.now().isoformat()
                })
            except Exception as update_err:
                # NO silenciar - registrar el error pero continuar (no es crítico para el flujo)
                logger.warning(
                    f"[WEBPAY] ERROR al actualizar gateway_response con commit_response: {type(update_err).__name__}: {str(update_err)}"
                )

            # Verificar respuesta
            response_code = response.get('response_code')
            is_approved = response_code == 0  # 0 = Transacción aprobada

            if is_approved:
                # PAGO EXITOSO
                logger.info(f"Pago aprobado para orden {order.id}")

                # Actualizar transacción de BD
                db_transaction.status = 'approved'
                db_transaction.webpay_authorization_code = response.get('authorization_code')
                
                # Usar fecha de la respuesta si está disponible
                transaction_date = response.get('transaction_date')
                if transaction_date:
                    from django.utils.dateparse import parse_datetime
                    try:
                        db_transaction.webpay_transaction_date = parse_datetime(transaction_date)
                    except (ValueError, TypeError) as date_err:
                        # NO silenciar - registrar el error pero usar fecha actual como fallback
                        logger.warning(
                            f"[WEBPAY] No se pudo parsear transaction_date '{transaction_date}': {str(date_err)}"
                        )
                        db_transaction.webpay_transaction_date = timezone.now()
                else:
                    db_transaction.webpay_transaction_date = timezone.now()
                
                card_detail = response.get('card_detail', {})
                if card_detail:
                    card_number = card_detail.get('card_number', '')
                    if card_number:
                        db_transaction.card_last_four = str(card_number)[-4:]
                    # Mapear card_type a formato más legible
                    card_type = card_detail.get('card_type', 'unknown')
                    if card_type == 'CR':
                        db_transaction.card_brand = 'Crédito'
                    elif card_type == 'DR':
                        db_transaction.card_brand = 'Débito'
                    else:
                        db_transaction.card_brand = card_type
                
                db_transaction.save()
                logger.info(f"[WEBPAY] PaymentTransaction actualizada: ID={db_transaction.id}")

                # Actualizar Payment
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment.status = PaymentStatus.objects.get(code='CAPTURED')
                    payment.save()
                    logger.info(f"[WEBPAY] Payment actualizado a CAPTURED")

                # Actualizar Order a PAID
                paid_status = OrderStatus.objects.get(code='PAID')
                order.status = paid_status
                order.save()
                logger.info(f"[WEBPAY] Order {order.id} actualizada a PAID")

                # Confirmar venta de productos (decrementar stock)
                for order_item in order.items.all():
                    product = order_item.product
                    product.confirm_sale(order_item.quantity)
                    logger.info(f"Stock confirmado para producto {product.id}: -{order_item.quantity}")

                # Enviar email de confirmación
                try:
                    send_order_confirmation_email(order)
                    logger.info(f"[WEBPAY] Email de confirmación enviado")
                except Exception as e:
                    logger.error(f"[WEBPAY] Error enviando email: {str(e)}")

                return True, "Pago confirmado exitosamente", {
                    'order_id': order.id,
                    'status': 'approved',
                    'authorization_code': db_transaction.webpay_authorization_code,
                    'amount': db_transaction.amount,
                    'card_last_four': db_transaction.card_last_four
                }

            else:
                # PAGO RECHAZADO
                logger.warning(f"Pago rechazado para orden {order.id}. Code: {response_code}")

                db_transaction.status = 'rejected'
                db_transaction.save(update_fields=['status'])
                # Actualizar gateway_response usando raw SQL
                try:
                    self._update_gateway_response(db_transaction.id, {
                        'rejection_reason': str(response_code)
                    })
                except Exception as update_err:
                    # NO silenciar - registrar el error pero continuar
                    logger.error(
                        f"[WEBPAY] ERROR al actualizar gateway_response después de rechazo: {type(update_err).__name__}: {str(update_err)}"
                    )

                # Actualizar Payment
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment.status = PaymentStatus.objects.get(code='FAILED')
                    payment.save()

                # Actualizar Order a FAILED
                failed_status = OrderStatus.objects.get(code='FAILED')
                order.status = failed_status
                order.save()

                # Liberar stock reservado
                for order_item in order.items.all():
                    product = order_item.product
                    product.release_stock(
                        quantity=order_item.quantity,
                        reason='Payment rejected',
                        reference_id=order.id
                    )
                    logger.info(f"Stock liberado para producto {product.id}: +{order_item.quantity}")

                return False, f"Pago rechazado (código: {response_code})", {
                    'order_id': order.id,
                    'status': 'rejected',
                    'response_code': response_code
                }

        except Exception as e:
            # Verificar si es un error de Transbank
            try:
                TransbankError, _ = _get_transbank_imports()
                if isinstance(e, TransbankError):
                    logger.error(f"[WEBPAY] ERROR TRANSBANK AL CONFIRMAR: {type(e).__name__}")
                    logger.error(f"[WEBPAY] Mensaje de error: {str(e)}", exc_info=True)
                    if db_transaction:
                        db_transaction.status = 'failed'
                        db_transaction.save(update_fields=['status'])
                        # Actualizar gateway_response usando raw SQL
                        try:
                            self._update_gateway_response(db_transaction.id, {
                                'error': str(e),
                                'error_type': type(e).__name__
                            })
                        except Exception as update_err:
                            # NO silenciar - registrar el error pero continuar
                            logger.error(
                                f"[WEBPAY] ERROR al actualizar gateway_response después de error Transbank: {type(update_err).__name__}: {str(update_err)}"
                            )
                    return False, f"Error de Transbank: {str(e)}", None
            except ImportError as import_err:
                # NO silenciar - registrar el error de importación
                logger.error(f"[WEBPAY] ERROR: No se pudo importar TransbankError para verificar tipo de error")
                logger.error(f"[WEBPAY] Error de importación: {str(import_err)}", exc_info=True)
            
            # Error inesperado
            logger.error(f"[WEBPAY] Error inesperado al confirmar transacción: {str(e)}", exc_info=True)
            if db_transaction:
                db_transaction.status = 'failed'
                db_transaction.save(update_fields=['status'])
                # Actualizar gateway_response usando raw SQL
                try:
                    self._update_gateway_response(db_transaction.id, {
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                except Exception as update_err:
                    # NO silenciar - registrar el error pero continuar
                    logger.error(
                        f"[WEBPAY] ERROR al actualizar gateway_response después de error interno: {type(update_err).__name__}: {str(update_err)}"
                    )
            return False, f"Error interno: {str(e)}", None


# Instancia global del servicio - se crea solo si transbank está disponible
# Si no está disponible, webpay_service será None y Django iniciará normalmente
# El error se mostrará cuando se intente usar Webpay
webpay_service = None
try:
    available, error = _check_transbank()
    if available:
        webpay_service = WebpayService()
        logger.info("WebpayService inicializado correctamente")
    else:
        logger.warning(f"transbank-sdk no está disponible. Error: {error}. Webpay no funcionará.")
except Exception as e:
    logger.error(f"Error al inicializar WebpayService: {str(e)}", exc_info=True)
    webpay_service = None

