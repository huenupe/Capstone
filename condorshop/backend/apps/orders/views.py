from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer, CreateOrderSerializer
from .services import send_order_confirmation_email
from apps.cart.models import Cart, CartItem
from apps.products.models import Product


def calculate_shipping_cost(subtotal):
    """Calcula el costo de envío"""
    if subtotal >= 50000:
        return 0
    return 5000


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
    shipping_cost = calculate_shipping_cost(subtotal)
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

