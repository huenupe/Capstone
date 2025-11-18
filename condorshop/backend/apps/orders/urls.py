from django.urls import path
from . import views

# Nota: app_name se omite porque este archivo se incluye en múltiples rutas
# (api/checkout/ y api/orders/), lo que causaría conflictos de namespace

urlpatterns = [
    # Checkout endpoints
    path('mode', views.checkout_mode, name='checkout-mode'),
    path('shipping-quote', views.shipping_quote, name='shipping-quote'),
    path('create', views.create_order, name='create-order'),
    # Order history endpoints (for authenticated users)
    path('', views.list_user_orders, name='list-orders'),
    path('<int:order_id>/', views.get_order_detail, name='order-detail'),
    # Webpay payment endpoint
    path('<int:order_id>/pay/', views.initiate_webpay_payment, name='initiate-payment'),
    # Cancel order endpoint
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel-order'),
]

