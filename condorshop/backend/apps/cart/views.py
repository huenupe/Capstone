from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
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


def get_cart_optimized(request):
    """
    Helper para obtener o crear carrito con prefetch optimizado.
    Usar solo en view_cart() para evitar recarga innecesaria.
    
    ✅ OPTIMIZACIÓN: Hace prefetch directamente en la búsqueda inicial,
    evitando la query adicional .get(id=cart.id) después de get_or_create_cart().
    """
    from django.db.models import Prefetch
    from apps.products.models import ProductImage
    
    # Preparar prefetch optimizado para imágenes (ordenadas por position)
    images_prefetch = Prefetch(
        'items__product__images',
        queryset=ProductImage.objects.order_by('position'),
        to_attr='ordered_images_for_product'
    )
    
    # Queryset base optimizado
    optimized_queryset = Cart.objects.select_related('user').prefetch_related(
        'items__product__category',
        images_prefetch
    )
    
    if request.user.is_authenticated:
        # ✅ OPTIMIZACIÓN: Buscar carrito activo con prefetch directamente
        # en lugar de buscar primero y luego recargar
        cart = optimized_queryset.filter(
            user=request.user, 
            is_active=True
        ).order_by('-created_at').first()
        
        if not cart:
            # Si no existe, crear y luego recargar con prefetch (única query adicional necesaria)
            cart, _ = Cart.get_or_create_cart(user=request.user)
            cart = optimized_queryset.get(id=cart.id)
        
        return cart, None
    else:
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            import uuid
            session_token = str(uuid.uuid4())
        
        # ✅ OPTIMIZACIÓN: Buscar carrito activo con prefetch directamente
        cart = optimized_queryset.filter(
            session_token=session_token,
            is_active=True
        ).order_by('-created_at').first()
        
        if not cart:
            # Si no existe, crear y luego recargar con prefetch
            cart, _ = Cart.get_or_create_cart(session_token=session_token)
            cart = optimized_queryset.get(id=cart.id)
        
        return cart, session_token


@api_view(['POST'])
@permission_classes([AllowAny])
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

    # Transacción atómica para evitar condiciones de carrera en el manejo de stock
    # Usa select_for_update() para bloquear la fila del producto mientras se valida y actualiza
    with transaction.atomic():
        try:
            # Bloquear la fila del producto para prevenir race conditions
            # Mientras esta transacción está activa, otras operaciones sobre el mismo producto esperarán
            product = Product.objects.select_for_update().get(id=product_id, active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar stock dentro de la transacción
        if product.stock_qty < quantity:
            return Response(
                {'error': f'Stock insuficiente. Disponible: {product.stock_qty}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, session_token = get_cart(request)

        # Usar final_price (precio con descuento si existe)
        unit_price = int(product.final_price)
        
        # Verificar si el producto ya está en el carrito
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': unit_price * quantity,
            }
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
            cart_item.unit_price = unit_price  # Actualizar precio (puede haber cambiado por descuento)
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
@permission_classes([AllowAny])
def view_cart(request):
    """
    Ver carrito del usuario/sesión
    GET /api/cart/
    Actualiza automáticamente los precios de los items si han cambiado (por descuentos)
    
    ✅ OPTIMIZACIÓN: Reducir tiempo bajo lock moviendo lógica no crítica fuera de transaction.atomic()
    La actualización de precios NO requiere transacción atómica estricta porque:
    - Es idempotente (múltiples actualizaciones dan el mismo resultado)
    - No hay riesgo de inconsistencia si falla (solo afecta precios mostrados)
    - El lock solo es necesario para evitar updates concurrentes del mismo item
    """
    import time
    import logging
    
    logger = logging.getLogger('performance')
    start_time = time.time()
    
    # ✅ OPTIMIZACIÓN: Usar get_cart_optimized para evitar recarga innecesaria
    cart, session_token = get_cart_optimized(request)
    
    # ✅ OPTIMIZACIÓN: Actualizar precios FUERA de transaction.atomic()
    # Solo usar atomic si realmente hay items a actualizar (reducir tiempo de lock)
    items_to_update = []
    for item in cart.items.all():
        if item.product:
            # Recalcular precio final del producto (property, no query)
            new_unit_price = item.product.final_price
            # Solo actualizar si el precio cambió (para evitar updates innecesarios)
            if item.unit_price != new_unit_price:
                item.unit_price = new_unit_price
                item.total_price = item.unit_price * item.quantity
                items_to_update.append(item)
    
    # ✅ OPTIMIZACIÓN: Solo usar transaction.atomic() si hay items a actualizar
    # Esto reduce el tiempo bajo lock cuando no hay cambios de precio
    if items_to_update:
        # Lock solo para el bulk_update (operación crítica)
        with transaction.atomic():
            CartItem.objects.bulk_update(items_to_update, ['unit_price', 'total_price'])
    
    serializer = CartSerializer(cart)
    response = Response(serializer.data)
    
    if session_token:
        response['X-Session-Token'] = session_token
    
    # ✅ OPTIMIZACIÓN: Logging de performance (solo en desarrollo o si tarda >500ms)
    duration = time.time() - start_time
    if duration > 0.5 or settings.DEBUG:
        from django.db import connection
        queries_count = len(connection.queries)
        queries_time = sum(float(q['time']) for q in connection.queries)
        logger.info(
            f"view_cart: {duration:.3f}s total, {queries_count} queries, {queries_time:.3f}s queries, "
            f"items={len(cart.items.all())}, updates={len(items_to_update)}"
        )
    
    return response


@api_view(['PATCH'])
@permission_classes([AllowAny])
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

    # Transacción atómica para evitar condiciones de carrera en el manejo de stock
    # Usa select_for_update() para bloquear tanto el CartItem como el Product relacionado
    with transaction.atomic():
        try:
            # Bloquear la fila del CartItem con el Product relacionado
            # select_related('product') evita N+1 query
            cart_item = CartItem.objects.select_related('product').select_for_update().get(
                id=item_id,
                cart=cart
            )
            # Bloquear explícitamente el Product para asegurar consistencia de stock
            # Esto previene que otro proceso modifique el stock mientras validamos
            Product.objects.select_for_update().get(id=cart_item.product.id)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado en el carrito'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar stock dentro de la transacción
        if cart_item.product.stock_qty < quantity:
            return Response(
                {'error': f'Stock insuficiente. Disponible: {cart_item.product.stock_qty}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.total_price = cart_item.unit_price * quantity
        cart_item.save()

    # ✅ CORRECCIÓN: Devolver el item actualizado para que el frontend pueda sincronizar
    from .serializers import CartItemSerializer
    serializer = CartItemSerializer(cart_item)
    
    response = Response({
        'message': 'Item actualizado',
        'item': serializer.data
    })
    if session_token:
        response['X-Session-Token'] = session_token
    
    return response


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_cart_item(request, item_id):
    """
    Eliminar item del carrito
    DELETE /api/cart/items/{id}/delete
    """
    cart, session_token = get_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        response = Response({'message': 'Item eliminado'}, status=status.HTTP_204_NO_CONTENT)
        if session_token:
            response['X-Session-Token'] = session_token
        return response
    except CartItem.DoesNotExist:
        # Si el item ya no existe, considerarlo como éxito (idempotente)
        # Esto evita errores cuando el frontend hace múltiples peticiones
        response = Response({'message': 'Item ya eliminado'}, status=status.HTTP_200_OK)
        if session_token:
            response['X-Session-Token'] = session_token
        return response

