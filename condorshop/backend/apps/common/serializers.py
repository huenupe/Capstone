"""
Serializers para apps.common
"""
from rest_framework import serializers
from .models import HeroCarouselSlide


class HeroCarouselSlideSerializer(serializers.ModelSerializer):
    """
    Serializer para slides del carrusel principal
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HeroCarouselSlide
        fields = ['id', 'name', 'description', 'image_url', 'alt_text', 'order']
        read_only_fields = ['id', 'order']
    
    def get_image_url(self, obj):
        """Retorna la URL absoluta de la imagen"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

