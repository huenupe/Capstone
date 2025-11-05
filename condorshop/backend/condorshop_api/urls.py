"""
URL configuration for condorshop_api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse

# Personalizar el AdminSite
admin.site.site_header = "CondorShop - Administración"
admin.site.site_title = "CondorShop - Administración"
admin.site.index_title = "Panel de Administración"

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

def favicon_view(request):
    """Serve favicon.ico for root and API endpoints"""
    import os
    # Try admin favicon first (for admin panel)
    admin_favicon = os.path.join(settings.STATICFILES_DIRS[0], 'admin', 'img', 'favicon.ico')
    if os.path.exists(admin_favicon):
        favicon_path = admin_favicon
    else:
        # Fallback to root favicon
        favicon_path = os.path.join(settings.STATICFILES_DIRS[0], 'favicon.ico')
    try:
        with open(favicon_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/x-icon')
    except FileNotFoundError:
        return HttpResponse(status=404)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('favicon.ico', favicon_view, name='favicon'),
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
    # Serve static files in development
    if settings.STATICFILES_DIRS:
        from django.contrib.staticfiles.urls import staticfiles_urlpatterns
        urlpatterns += staticfiles_urlpatterns()

