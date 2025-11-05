from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product, Category
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    CategorySerializer
)
from .filters import ProductFilter


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para productos
    - GET /api/products/ - Listado con búsqueda, filtros y ordenamiento
    - GET /api/products/{slug}/ - Detalle por slug
    """
    queryset = Product.objects.filter(active=True).select_related('category').prefetch_related('images')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']
    lookup_field = 'slug'

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


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para categorías
    GET /api/products/categories/ - Listado de categorías
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

