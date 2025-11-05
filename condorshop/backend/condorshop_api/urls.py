"""
URL configuration for condorshop_api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """API root endpoint with available routes"""
    return JsonResponse({
        'name': 'CondorShop API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'products': '/api/products/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'checkout': '/api/checkout/',
            'admin_panel': '/api/admin/',
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/checkout/', include('apps.orders.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

