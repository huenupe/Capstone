from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer, CreateOrderSerializer
from .services import evaluate_shipping, send_order_confirmation_email
from apps.cart.models import Cart
from apps.products.models import Product


def calculate_shipping_cost(subtotal, region=None, cart_items=None):
    """Calcular costo de envío utilizando la lógica centralizada."""
    evaluation = evaluate_shipping(region, subtotal, cart_items)
    return evaluation['cost']


def get_shipping_quote(region, subtotal, cart_items):
    """Obtener cotización de envío reutilizando la evaluación centralizada."""
    evaluation = evaluate_shipping(region, subtotal, cart_items)
    threshold = evaluation['free_shipping_threshold']

    return {
        'cost': int(evaluation['cost']),
        'free_shipping_threshold': int(threshold) if threshold is not None else None,
        'zone': evaluation['zone'],
        'carrier': evaluation.get('carrier'),
        'applied_rule_id': evaluation.get('applied_rule_id'),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='20/m', method='POST')
def shipping_quote(request):
    """
    Obtener cotización de envío
    POST /api/checkout/shipping-quote
    Body: { "region": "...", "cart_items": [{ "product_id": 1, "quantity": 2 }] }
    """
    region = request.data.get('region')
    cart_items_data = request.data.get('cart_items', [])
    subtotal = request.data.get('subtotal', 0)
    
    if not region:
        return Response(
            {'error': 'La región es requerida'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build item list for shipping calculation
    items_for_calc = []
    for item_data in cart_items_data:
        product_id = item_data.get('product_id')
        if not product_id:
            continue
        
        try:
            product = Product.objects.select_related('category').get(id=product_id)
            items_for_calc.append(type('Item', (), {
                'product_id': product_id,
                'product': product,
            })())
        except Product.DoesNotExist:
            continue
    
    if len(items_for_calc) != len(cart_items_data):
        return Response({'error': 'Datos de carrito inválidos'}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate subtotal if not provided
    if not subtotal and items_for_calc:
        subtotal = 0
        for item_data, calc in zip(cart_items_data, items_for_calc):
            quantity = item_data.get('quantity', 1)
            subtotal += calc.product.price * quantity
    
    quote = get_shipping_quote(region, subtotal, items_for_calc)
    return Response(quote)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def checkout_mode(request):
    """
    Informa el modo de checkout
    GET /api/checkout/mode
    Retorna información sobre direcciones guardadas del usuario
    """
    user = request.user if request.user.is_authenticated else None
    has_address = False
    saved_addresses = []
    
    if user:
    # Check legacy address fields
        has_address = bool(user.street and user.city and user.region)
        
        # Load saved addresses
        try:
            from apps.users.models import Address
            addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')
            from apps.users.serializers import AddressSerializer
            saved_addresses = AddressSerializer(addresses, many=True).data
        except Exception:
            pass  # best-effort if the Address model is unavailable
    
    return Response({
        'is_authenticated': user is not None,
        'has_address': has_address,
        'saved_addresses': saved_addresses,
        'user_email': user.email if user else None
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='user', rate='10/h', method='POST')
@transaction.atomic
def create_order(request):
    """
    Crear pedido desde el carrito
    POST /api/orders/create
    """
    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Obtener carrito
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user, is_active=True)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Carrito no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            return Response(
                {'error': 'Token de sesión requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            cart = Cart.objects.get(session_token=session_token, is_active=True)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Carrito no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    cart_items_qs = cart.items.select_related('product').all()
    if not cart_items_qs.exists():
        return Response(
            {'error': 'El carrito está vacío'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart_items = list(cart_items_qs)
    item_payloads = []
    subtotal = 0

    product_ids = [item.product_id for item in cart_items]
    products_map = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    if len(products_map) != len(product_ids):
        missing = sorted(set(product_ids) - set(products_map.keys()))
        return Response(
            {
                'error': 'Algunos productos del carrito no están disponibles',
                'missing_product_ids': missing,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ANTES de crear Order, reservar stock
    reserved_products = []  # Para liberar si falla
    
    try:
        with transaction.atomic():
            for cart_item in cart_items:
                product = products_map[cart_item.product_id]
                
                # Reservar stock (con validación)
                try:
                    product.reserve_stock(
                        quantity=cart_item.quantity,
                        reason='Order pending',
                        reference_id=None  # Se actualizará después de crear Order
                    )
                    reserved_products.append((product, cart_item.quantity))
                except ValidationError as e:
                    # Liberar reservas anteriores si falla
                    for prev_product, prev_quantity in reserved_products:
                        try:
                            prev_product.release_stock(prev_quantity, reason='Order creation failed')
                        except Exception:
                            pass
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                unit_price = int(product.final_price)
                quantity = int(cart_item.quantity)
                total_price = unit_price * quantity
                subtotal += total_price

                item_payloads.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                })
    except Exception as e:
        # Liberar todas las reservas si hay error
        for prev_product, prev_quantity in reserved_products:
            try:
                prev_product.release_stock(prev_quantity, reason='Order creation failed')
            except Exception:
                pass
        return Response(
            {'error': f'Error al reservar stock: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    shipping_region = serializer.validated_data.get('shipping_region', '')
    shipping_cost = int(calculate_shipping_cost(subtotal, shipping_region, cart_items))
    total_amount = subtotal + shipping_cost

    # Obtener estado PENDING
    pending_status = OrderStatus.objects.get(code='PENDING')

    # NUEVO: Crear snapshot de envío antes de crear Order
    from apps.orders.models import OrderShippingSnapshot
    from apps.users.models import Address
    
    snapshot_data = serializer.validated_data.copy()
    
    # Obtener datos del usuario si está autenticado
    original_user = request.user if request.user.is_authenticated else None
    original_address = None
    
    if original_user:
        # Intentar obtener dirección guardada si existe
        address_label = serializer.validated_data.get('address_label')
        if address_label:
            try:
                original_address = Address.objects.get(
                    user=original_user,
                    label=address_label
                )
            except Address.DoesNotExist:
                pass
        
        # Si no hay dirección guardada, intentar obtener datos del usuario
        if not snapshot_data.get('customer_name') and original_user:
            snapshot_data['customer_name'] = (
                original_user.get_full_name() or 
                original_user.username or 
                original_user.email
            )
        if not snapshot_data.get('customer_email') and original_user:
            snapshot_data['customer_email'] = original_user.email
        if not snapshot_data.get('customer_phone') and hasattr(original_user, 'phone'):
            snapshot_data['customer_phone'] = original_user.phone or ''
    
    # Crear snapshot
    shipping_snapshot = OrderShippingSnapshot.objects.create(
        customer_name=snapshot_data['customer_name'],
        customer_email=snapshot_data['customer_email'],
        customer_phone=snapshot_data.get('customer_phone', ''),
        shipping_street=snapshot_data['shipping_street'],
        shipping_city=snapshot_data['shipping_city'],
        shipping_region=snapshot_data['shipping_region'],
        shipping_postal_code=snapshot_data.get('shipping_postal_code', ''),
        shipping_country='Chile',
        original_user=original_user,
        original_address=original_address
    )

    # Crear orden vinculada al snapshot
    order = Order.objects.create(
        user=original_user,
        status=pending_status,
        shipping_snapshot=shipping_snapshot,
        total_amount=total_amount,
        shipping_cost=shipping_cost,
        currency='CLP'
    )

    # Crear items de la orden con snapshots
    from apps.orders.models import OrderItemSnapshot
    
    order_items = []
    for payload in item_payloads:
        product = payload['product']
        
        # Crear snapshot del producto
        product_category_name = product.category.name if product.category else None
        price_snapshot = OrderItemSnapshot.objects.create(
            product_name=product.name,
            product_sku=product.sku,
            product_id=product.id,
            unit_price=payload['unit_price'],
            total_price=payload['total_price'],
            product_brand=product.brand,
            product_category_name=product_category_name,
        )
        
        # Crear item vinculado al snapshot
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=payload['quantity'],
            unit_price=payload['unit_price'],
            total_price=payload['total_price'],
            price_snapshot=price_snapshot,
        )
        order_items.append(order_item)
    
    OrderItem.objects.bulk_create(order_items)

    # Después de crear Order, actualizar reference_id en movimientos de inventario
    from apps.products.models import InventoryMovement
    for item in order_items:
        try:
            movements = item.product.inventory_movements.filter(
                movement_type='reserve',
                reference_id__isnull=True
            ).order_by('-created_at')[:1]
            for movement in movements:
                movement.reference_id = order.id
                movement.reference_type = 'order'
                movement.save()
        except Exception:
            pass

    # Registrar historial de estado
    from .models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=order,
        status=pending_status,
        changed_by=request.user if request.user.is_authenticated else None,
        note='Orden creada'
    )

    # Desactivar carrito
    cart.is_active = False
    cart.save()
    
    # Guardar dirección si el usuario está autenticado y lo solicitó
    if original_user and serializer.validated_data.get('save_address'):
        try:
            address_data = {
                'user': original_user,
                'label': serializer.validated_data.get('address_label') or None,
                'street': snapshot_data['shipping_street'],
                'city': snapshot_data['shipping_city'],
                'region': snapshot_data['shipping_region'],
                'postal_code': snapshot_data.get('shipping_postal_code') or None,
                'is_default': False  # No marcar como default automáticamente
            }
            # Extraer número y apartamento si están en la calle (opcional)
            # Por ahora guardamos la calle completa, pero se puede mejorar
            Address.objects.create(**address_data)
        except Exception as e:
            # No fallar la orden si falla guardar la dirección
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error saving address for order {order.id}: {e}')

    # Preparar email de confirmación (se enviará cuando se integre Webpay)
    # send_order_confirmation_email(order)
    
    # Preparar respuesta
    response_serializer = OrderSerializer(order)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_orders(request):
    """
    Listar pedidos del usuario autenticado
    GET /api/orders/
    """
    orders = Order.objects.filter(user=request.user).select_related(
        'status'
    ).prefetch_related('items__product', 'status_history').order_by('-created_at')
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_id):
    """
    Obtener detalle de un pedido del usuario autenticado
    GET /api/orders/{id}/
    """
    try:
        order = Order.objects.select_related('status').prefetch_related(
            'items__product', 'status_history'
        ).get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)

