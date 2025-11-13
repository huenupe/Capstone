from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
# Registrar primero las categorías para evitar que el r'' del product capture el prefijo
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]

