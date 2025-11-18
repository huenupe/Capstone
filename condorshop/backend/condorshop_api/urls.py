"""
URL configuration for condorshop_api project.
"""
from django.contrib import admin
from django.contrib.auth.views import redirect_to_login
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError
from django.views.decorators.cache import never_cache

# Personalizar el AdminSite
admin.site.site_header = "CondorShop - Administración"
admin.site.site_title = "CondorShop - Administración"
admin.site.index_title = "Panel de Administración"


@never_cache
def api_root(request):
    """API root endpoint with available routes (redirige al admin en desarrollo)."""
    if settings.DEBUG:
        login_url = reverse('admin:login')
        response = redirect_to_login('/admin/', login_url=login_url)
        response['Cache-Control'] = 'no-store, max-age=0'
        response['Pragma'] = 'no-cache'
        return response

    return JsonResponse({
        'name': 'CondorShop API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health/',
            'admin': '/admin/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'products': '/api/products/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'checkout': '/api/checkout/',
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


def health_check(request):
    """Lightweight health-check endpoint for liveness/readiness probes."""
    status_code = 200
    checks = {}

    try:
        connection.ensure_connection()
        checks['database'] = 'ok'
    except OperationalError:
        checks['database'] = 'error'
        status_code = 503

    payload = {
        'status': 'ok' if status_code == 200 else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }
    return JsonResponse(payload, status=status_code)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/checkout/', include('apps.orders.urls')),
    path('api/orders/', include('apps.orders.urls')),
    # APIs de pagos (callbacks de Webpay)
    path('api/payments/', include('apps.orders.payment_urls')),
]

if settings.DEBUG:
    # Servir archivos media con headers de caché optimizados para mejorar rendimiento
    def serve_media_with_cache(request, path, document_root=None):
        """Servir archivos media con headers de caché para mejorar rendimiento"""
        response = serve(request, path, document_root=document_root)
        # Agregar headers de caché para imágenes (1 año para archivos estáticos)
        if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        return response
    
    # Reemplazar el static() por defecto con nuestra versión con caché
    urlpatterns += [
        path(f'{settings.MEDIA_URL.lstrip("/")}<path:path>', 
             lambda request, path: serve_media_with_cache(request, path, document_root=settings.MEDIA_ROOT)),
    ]
    # Serve static files in development
    if settings.STATICFILES_DIRS:
        from django.contrib.staticfiles.urls import staticfiles_urlpatterns
        urlpatterns += staticfiles_urlpatterns()

