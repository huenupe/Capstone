"""
Views para apps.common
"""
import logging
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import HeroCarouselSlide
from .serializers import HeroCarouselSlideSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def hero_carousel_slides(request):
    """
    Obtiene todos los slides activos del carrusel principal
    Ordenados por el campo 'order'
    Con caché de 15 minutos
    
    GET /api/common/hero-carousel/
    """
    cache_key = 'hero_carousel_slides'
    
    # Intentar obtener desde caché
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.debug("Carrusel obtenido desde caché")
        return Response(cached_data, status=status.HTTP_200_OK)
    
    try:
        slides = HeroCarouselSlide.objects.filter(is_active=True).order_by('order', 'created_at')
        serializer = HeroCarouselSlideSerializer(slides, many=True, context={'request': request})
        data = serializer.data
        
        # Guardar en caché por 15 minutos
        cache.set(cache_key, data, timeout=60 * 15)
        logger.debug(f"Carrusel obtenido de BD y guardado en caché ({len(data)} slides)")
        
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al obtener slides del carrusel: {type(e).__name__}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Error al cargar slides del carrusel'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

