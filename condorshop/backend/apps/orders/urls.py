from django.urls import path
from . import views

urlpatterns = [
    # Checkout endpoints
    path('mode', views.checkout_mode, name='checkout_mode'),
    path('create', views.create_order, name='create_order'),
    # Order history endpoints (for authenticated users)
    path('', views.list_user_orders, name='list_user_orders'),
    path('<int:order_id>/', views.get_order_detail, name='get_order_detail'),
]

