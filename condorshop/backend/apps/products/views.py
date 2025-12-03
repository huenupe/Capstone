from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from apps.common.utils import format_clp
from .models import Product, Category, ProductPriceHistory, ProductImage
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    CategorySerializer,
    ProductPriceHistorySerializer
)
from .filters import ProductFilter


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para productos
    - GET /api/products/ - Listado con búsqueda, filtros y ordenamiento
    - GET /api/products/{slug}/ - Detalle por slug
    
    Optimización: Endpoint list cacheado por 5 minutos para mejorar LCP.
    Caché se invalida automáticamente cuando se crean/actualizan/eliminan productos.
    """
    queryset = Product.objects.filter(active=True).select_related('category').prefetch_related(
        # ✅ OPTIMIZACIÓN: Prefetch imágenes ordenadas por position para evitar queries adicionales
        Prefetch(
            'images',
            queryset=ProductImage.objects.order_by('position'),
            to_attr='ordered_images'
        )
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    @method_decorator(cache_page(300))  # Cachear 5 minutos (300 segundos)
    def list(self, request, *args, **kwargs):
        """
        Listado de productos cacheado para mejorar rendimiento.
        Caché se invalida automáticamente cuando hay cambios en productos.
        """
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def get_serializer_context(self):
        """Pasar el request al serializer para construir URLs absolutas"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        # Búsqueda en nombre y descripción
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['get'], url_path='price-history')
    def price_history(self, request, slug=None):
        """
        Endpoint opcional para consultar historial de precios de un producto.
        GET /api/products/{slug}/price-history/
        """
        product = get_object_or_404(Product, slug=slug, active=True)
        history = ProductPriceHistory.objects.filter(product=product).order_by('-effective_from')
        
        # Opcional: limitar cantidad de registros
        limit = request.query_params.get('limit', None)
        if limit:
            try:
                limit = int(limit)
                history = history[:limit]
            except ValueError:
                pass
        
        serializer = ProductPriceHistorySerializer(history, many=True, context={'request': request})
        return Response({
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'current_price': product.final_price,
                'current_price_formatted': format_clp(product.final_price)
            },
            'history': serializer.data,
            'total_records': history.count()
        })


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para categorías
    GET /api/products/categories/ - Listado de categorías con jerarquía
    GET /api/products/categories/{id}/ - Detalle de categoría con subcategorías
    
    Optimización: Endpoint list cacheado por 15 minutos ya que categorías cambian raramente.
    Caché se invalida automáticamente cuando se crean/actualizan/eliminan categorías.
    """
    queryset = Category.objects.select_related('parent_category').prefetch_related(
        # ✅ OPTIMIZACIÓN: Prefetch subcategorías activas ordenadas para evitar N+1 queries
        Prefetch(
            'subcategories',
            queryset=Category.objects.filter(active=True).order_by('sort_order', 'name'),
            to_attr='active_subcategories'
        )
    )
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @method_decorator(cache_page(900))  # Cachear 15 minutos (900 segundos) - categorías cambian raramente
    def list(self, request, *args, **kwargs):
        """
        Listado de categorías cacheado para mejorar rendimiento.
        Caché se invalida automáticamente cuando hay cambios en categorías.
        """
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Optimizar queries con jerarquía"""
        queryset = super().get_queryset()
        # Opcional: filtrar solo categorías raíz si se solicita
        root_only = self.request.query_params.get('root_only', None)
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent_category__isnull=True)
        return queryset
    
    @action(detail=True, methods=['get'], url_path='price-history')
    def price_history(self, request, pk=None):
        """
        Endpoint opcional para consultar historial de precios de un producto.
        GET /api/products/categories/{id}/price-history/
        """
        category = get_object_or_404(Category, pk=pk)
        # Este endpoint es para categorías, pero el historial es de productos
        # Por ahora retornamos vacío, pero se puede extender si es necesario
        return Response({'message': 'Use /api/products/{product_id}/price-history/ instead'}, status=status.HTTP_400_BAD_REQUEST)

