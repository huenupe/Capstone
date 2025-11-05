from rest_framework import serializers
from apps.products.models import Product, ProductImage
from apps.orders.models import Order, OrderStatus
from apps.products.serializers import ProductAdminSerializer, ProductImageSerializer


class ProductImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'url', 'alt_text', 'position')

