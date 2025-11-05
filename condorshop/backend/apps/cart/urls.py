from django.urls import path
from . import views

urlpatterns = [
    path('add', views.add_to_cart, name='add_to_cart'),
    path('', views.view_cart, name='view_cart'),
    path('items/<int:item_id>', views.update_cart_item, name='update_cart_item'),
    path('items/<int:item_id>/delete', views.remove_cart_item, name='remove_cart_item'),
]

