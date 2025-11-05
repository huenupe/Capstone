from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from decimal import Decimal
from .models import Order, OrderItem, OrderStatus, ShippingZone, ShippingRule
from .serializers import OrderSerializer, CreateOrderSerializer
from .services import send_order_confirmation_email
from apps.cart.models import Cart, CartItem
from apps.products.models import Product


def calculate_shipping_cost(subtotal, region=None, cart_items=None):
    """
    Calcula el costo de envío basado en reglas de shipping
    Si no hay reglas configuradas, usa la lógica por defecto (envío gratis sobre 50k)
    """
    # Si no hay región o items, usar lógica por defecto
    if not region or not cart_items:
        return Decimal('0.00') if subtotal >= 50000 else Decimal('5000.00')
    
    # Buscar zona de envío
    zone = None
    try:
        zone = ShippingZone.objects.filter(
            is_active=True,
            regions__icontains=region
        ).first()
    except Exception:
        pass
    
    # Obtener reglas activas (ordenadas por prioridad)
    rules = ShippingRule.objects.filter(is_active=True)
    
    # Filtrar por zona si existe
    if zone:
        rules = rules.filter(zone__in=[zone, None])  # Reglas de la zona o generales
    else:
        rules = rules.filter(zone__isnull=True)  # Solo reglas generales
    
    rules = rules.order_by('-priority', '-created_at')
    
    # Buscar regla aplicable
    applied_rule = None
    
    # Primero buscar reglas de PRODUCT
    product_ids = [item.product_id for item in cart_items if hasattr(item, 'product_id')]
    if not product_ids and hasattr(cart_items[0], 'product'):
        product_ids = [item.product.id for item in cart_items]
    
    product_rules = rules.filter(rule_type='PRODUCT', product_id__in=product_ids)
    if product_rules.exists():
        applied_rule = product_rules.first()
    else:
        # Buscar reglas de CATEGORY
        category_ids = []
        for item in cart_items:
            if hasattr(item, 'product') and item.product.category_id:
                category_ids.append(item.product.category_id)
            elif hasattr(item, 'product_id'):
                try:
                    product = Product.objects.get(id=item.product_id)
                    if product.category_id:
                        category_ids.append(product.category_id)
                except Product.DoesNotExist:
                    pass
        
        if category_ids:
            category_rules = rules.filter(rule_type='CATEGORY', category_id__in=category_ids)
            if category_rules.exists():
                applied_rule = category_rules.first()
        
        # Si no hay regla específica, usar regla ALL
        if not applied_rule:
            all_rules = rules.filter(rule_type='ALL')
            if all_rules.exists():
                applied_rule = all_rules.first()
    
    # Si hay regla aplicable, calcular costo
    if applied_rule:
        # Verificar umbral de envío gratis
        if applied_rule.free_shipping_threshold and subtotal >= applied_rule.free_shipping_threshold:
            return Decimal('0.00')
        return applied_rule.base_cost
    
    # Fallback: lógica por defecto
    return Decimal('0.00') if subtotal >= 50000 else Decimal('5000.00')


def get_shipping_quote(region, subtotal, cart_items):
    """
    Obtiene cotización de envío con información detallada
    Retorna: { cost, free_shipping_threshold, zone }
    """
    zone = None
    try:
        zone = ShippingZone.objects.filter(
            is_active=True,
            regions__icontains=region
        ).first()
    except Exception:
        pass
    
    rules = ShippingRule.objects.filter(is_active=True)
    if zone:
        rules = rules.filter(zone__in=[zone, None])
    else:
        rules = rules.filter(zone__isnull=True)
    
    rules = rules.order_by('-priority', '-created_at')
    
    applied_rule = None
    product_ids = []
    for item in cart_items:
        if hasattr(item, 'product_id'):
            product_ids.append(item.product_id)
        elif hasattr(item, 'product'):
            product_ids.append(item.product.id)
    
    product_rules = rules.filter(rule_type='PRODUCT', product_id__in=product_ids)
    if product_rules.exists():
        applied_rule = product_rules.first()
    else:
        category_ids = []
        for item in cart_items:
            product = None
            if hasattr(item, 'product'):
                product = item.product
            elif hasattr(item, 'product_id'):
                try:
                    product = Product.objects.select_related('category').get(id=item.product_id)
                except Product.DoesNotExist:
                    pass
            
            if product and product.category_id:
                category_ids.append(product.category_id)
        
        if category_ids:
            category_rules = rules.filter(rule_type='CATEGORY', category_id__in=category_ids)
            if category_rules.exists():
                applied_rule = category_rules.first()
        
        if not applied_rule:
            all_rules = rules.filter(rule_type='ALL')
            if all_rules.exists():
                applied_rule = all_rules.first()
    
    if applied_rule:
        cost = Decimal('0.00')
        if applied_rule.free_shipping_threshold and subtotal >= applied_rule.free_shipping_threshold:
            cost = Decimal('0.00')
        else:
            cost = applied_rule.base_cost
        
        return {
            'cost': float(cost),
            'free_shipping_threshold': float(applied_rule.free_shipping_threshold) if applied_rule.free_shipping_threshold else None,
            'zone': zone.name if zone else None,
            'rule_type': applied_rule.rule_type,
        }
    
    # Fallback
    default_threshold = 50000
    cost = Decimal('0.00') if subtotal >= default_threshold else Decimal('5000.00')
    return {
        'cost': float(cost),
        'free_shipping_threshold': default_threshold,
        'zone': None,
        'rule_type': 'DEFAULT',
    }


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
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
    
    # Construir lista de items para cálculo
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
    
    # Si no hay subtotal, calcularlo
    if not subtotal and items_for_calc:
        subtotal = sum(
            item.product.price * item_data.get('quantity', 1)
            for item, item_data in zip(items_for_calc, cart_items_data)
        )
    
    quote = get_shipping_quote(region, Decimal(str(subtotal)), items_for_calc)
    return Response(quote)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def checkout_mode(request):
    """
    Informa el modo de checkout
    GET /api/checkout/mode
    """
    user = request.user if request.user.is_authenticated else None
    has_address = False
    
    if user:
        has_address = bool(user.street and user.city and user.region)
    
    return Response({
        'is_authenticated': user is not None,
        'has_address': has_address,
        'user_email': user.email if user else None
    })


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
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

    cart_items = cart.items.select_related('product').all()
    if not cart_items.exists():
        return Response(
            {'error': 'El carrito está vacío'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validar stock y bloquear filas
    products_to_update = []
    items_data = []
    
    for cart_item in cart_items:
        # Bloquear la fila del producto para lectura con SELECT FOR UPDATE
        product = Product.objects.select_for_update().get(id=cart_item.product.id)
        
        if product.stock_qty < cart_item.quantity:
            return Response(
                {
                    'error': f'Stock insuficiente para {product.name}',
                    'available': product.stock_qty,
                    'required': cart_item.quantity
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Preparar para actualizar stock
        product.stock_qty -= cart_item.quantity
        products_to_update.append(product)
        
        # Preparar datos del item
        items_data.append({
            'product': product,
            'quantity': cart_item.quantity,
            'unit_price': cart_item.unit_price,
            'total_price': cart_item.quantity * cart_item.unit_price
        })

    # Calcular totales
    subtotal = sum(item['total_price'] for item in items_data)
    shipping_region = serializer.validated_data.get('shipping_region', '')
    shipping_cost = calculate_shipping_cost(subtotal, shipping_region, cart_items)
    total_amount = subtotal + shipping_cost

    # Obtener estado PENDING
    pending_status = OrderStatus.objects.get(code='PENDING')

    # Crear orden
    order_data = serializer.validated_data
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        status=pending_status,
        total_amount=total_amount,
        shipping_cost=shipping_cost,
        **order_data
    )

    # Crear items de la orden
    order_items = []
    for item_data in items_data:
        order_item = OrderItem.objects.create(
            order=order,
            product=item_data['product'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            total_price=item_data['total_price']
        )
        order_items.append(order_item)

    # Actualizar stock de productos
    for product in products_to_update:
        product.save()

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

