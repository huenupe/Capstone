from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, UpdateCartItemSerializer
from apps.products.models import Product


def get_cart(request):
    """Helper para obtener o crear carrito según usuario o sesión"""
    if request.user.is_authenticated:
        cart, _ = Cart.get_or_create_cart(user=request.user)
    else:
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            # Generar nuevo token
            import uuid
            session_token = str(uuid.uuid4())
        cart, _ = Cart.get_or_create_cart(session_token=session_token)
    return cart, session_token if not request.user.is_authenticated else None


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def add_to_cart(request):
    """
    Agregar producto al carrito
    POST /api/cart/add
    Body: { "product_id": 1, "quantity": 2 }
    """
    serializer = AddToCartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data['quantity']

    try:
        product = Product.objects.get(id=product_id, active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Validar stock
    if product.stock_qty < quantity:
        return Response(
            {'error': f'Stock insuficiente. Disponible: {product.stock_qty}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart, session_token = get_cart(request)

    # Verificar si el producto ya está en el carrito
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity, 'unit_price': product.price}
    )

    if not created:
        # Actualizar cantidad
        new_quantity = cart_item.quantity + quantity
        if product.stock_qty < new_quantity:
            return Response(
                {'error': f'Stock insuficiente. Disponible: {product.stock_qty}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.quantity = new_quantity
        cart_item.unit_price = product.price  # Actualizar precio por si cambió
        cart_item.save()

    response = Response(
        {'message': 'Producto agregado al carrito', 'cart_id': cart.id},
        status=status.HTTP_201_CREATED
    )
    
    # Incluir session_token en headers si es invitado
    if session_token:
        response['X-Session-Token'] = session_token
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def view_cart(request):
    """
    Ver carrito del usuario/sesión
    GET /api/cart/
    """
    cart, session_token = get_cart(request)
    serializer = CartSerializer(cart)
    response = Response(serializer.data)
    
    if session_token:
        response['X-Session-Token'] = session_token
    
    return response


@api_view(['PATCH'])
@permission_classes([IsAuthenticatedOrReadOnly])
def update_cart_item(request, item_id):
    """
    Actualizar cantidad de un item del carrito
    PATCH /api/cart/items/{id}
    Body: { "quantity": 3 }
    """
    serializer = UpdateCartItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    quantity = serializer.validated_data['quantity']
    cart, session_token = get_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response(
            {'error': 'Item no encontrado en el carrito'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Validar stock
    if cart_item.product.stock_qty < quantity:
        return Response(
            {'error': f'Stock insuficiente. Disponible: {cart_item.product.stock_qty}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart_item.quantity = quantity
    cart_item.save()

    response = Response({'message': 'Item actualizado'})
    if session_token:
        response['X-Session-Token'] = session_token
    
    return response


@api_view(['DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def remove_cart_item(request, item_id):
    """
    Eliminar item del carrito
    DELETE /api/cart/items/{id}
    """
    cart, session_token = get_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        return Response({'message': 'Item eliminado'}, status=status.HTTP_204_NO_CONTENT)
    except CartItem.DoesNotExist:
        return Response(
            {'error': 'Item no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

