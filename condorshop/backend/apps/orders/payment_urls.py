"""
URLs para callbacks de pasarelas de pago
Estas van en la raíz de la API
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('return/', views.webpay_return, name='webpay-return'),
    path('status/<int:order_id>/', views.payment_status, name='payment-status'),
]

