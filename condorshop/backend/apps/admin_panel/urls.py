from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductAdminViewSet, OrderAdminViewSet, OrderStatusViewSet

router = DefaultRouter()
router.register(r'products', ProductAdminViewSet, basename='admin-product')
router.register(r'orders', OrderAdminViewSet, basename='admin-order')
router.register(r'order-statuses', OrderStatusViewSet, basename='admin-order-status')

urlpatterns = [
    path('', include(router.urls)),
]

