import csv
import os
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from PIL import Image
from .permissions import IsAdmin
from apps.products.models import Product, ProductImage, Category
from apps.products.serializers import ProductAdminSerializer
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
from apps.orders.serializers import OrderAdminSerializer, OrderStatusSerializer
from apps.admin_panel.serializers import ProductImageUploadSerializer


class ProductAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD de productos para administradores
    GET/POST /api/admin/products
    GET/PATCH/DELETE /api/admin/products/{id}
    """
    queryset = Product.objects.all().select_related('category').prefetch_related('images')
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'active']

    def perform_create(self, serializer):
        """Crear producto"""
        serializer.save()

    def perform_update(self, serializer):
        """Actualizar producto"""
        serializer.save()

    @action(detail=True, methods=['post'], parser_classes=(MultiPartParser, FormParser))
    def images(self, request, pk=None):
        """
        Subir imagen a un producto
        POST /api/admin/products/{id}/images
        Body: form-data con 'image' file, 'alt_text' (opcional), 'position' (opcional)
        """
        product = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo de imagen'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Validar formato
        try:
            img = Image.open(image_file)
            if img.format not in ['JPEG', 'PNG']:
                return Response(
                    {'error': 'Formato no permitido. Use JPEG o PNG'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': 'Archivo inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar imagen
        media_path = os.path.join('products', f'{product.id}_{image_file.name}')
        full_path = os.path.join('media', media_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        # Crear registro en BD
        alt_text = request.data.get('alt_text', '')
        position = request.data.get('position', 0)
        
        product_image = ProductImage.objects.create(
            product=product,
            url=f'/media/{media_path}',
            alt_text=alt_text,
            position=int(position) if position else 0
        )
        
        serializer = ProductImageUploadSerializer(product_image)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Gestión de pedidos para administradores
    GET /api/admin/orders - Lista con filtros
    GET /api/admin/orders/{id} - Detalle
    """
    queryset = Order.objects.all().select_related('status', 'user').prefetch_related('items', 'status_history')
    serializer_class = OrderAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'customer_email']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por rango de fechas
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """
        Cambiar estado de un pedido
        PATCH /api/admin/orders/{id}/status
        Body: { "status_id": 2, "note": "..." }
        """
        order = self.get_object()
        status_id = request.data.get('status_id')
        note = request.data.get('note', '')
        
        if not status_id:
            return Response(
                {'error': 'status_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_status = OrderStatus.objects.get(id=status_id)
        except OrderStatus.DoesNotExist:
            return Response(
                {'error': 'Estado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar transición de estado
        current_code = order.status.code
        new_code = new_status.code
        
        valid_transitions = {
            'PENDING': ['PREPARING', 'CANCELLED'],
            'PREPARING': ['SHIPPED'],
            'SHIPPED': ['DELIVERED'],
        }
        
        if current_code in valid_transitions:
            if new_code not in valid_transitions[current_code]:
                return Response(
                    {'error': f'Transición inválida: {current_code} -> {new_code}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif current_code != 'CANCELLED' and new_code == 'CANCELLED':
            # Cancelar solo si aún no está en preparación o después
            if current_code not in ['PENDING']:
                return Response(
                    {'error': 'No se puede cancelar un pedido en este estado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': f'Transición no permitida desde {current_code}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar estado
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Registrar en historial
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            changed_by=request.user,
            note=note or f'Cambio de {old_status.code} a {new_status.code}'
        )
        
        serializer = OrderAdminSerializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Exportar pedidos a CSV
        GET /api/admin/orders/export?status=1&date_from=2025-01-01
        """
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Fecha', 'Cliente', 'Email', 'Total', 'Estado', 'Ciudad', 'Región'])
        
        for order in queryset:
            writer.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.customer_name,
                order.customer_email,
                order.total_amount,
                order.status.code,
                order.shipping_city,
                order.shipping_region,
            ])
        
        return response


class OrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista de estados de pedido
    GET /api/admin/order-statuses
    """
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

