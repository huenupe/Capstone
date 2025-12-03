"""
Middleware para logging de performance de requests.
Solo activo en desarrollo o para requests lentos (>500ms).
"""
import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger('performance')


class PerformanceLoggingMiddleware:
    """
    Middleware que registra información de performance para requests lentos.
    
    ✅ OPTIMIZACIÓN: Solo loguea requests que tardan >500ms o en modo DEBUG
    para evitar sobrecarga en producción.
    
    Métricas registradas:
    - Tiempo total del request
    - Número de queries ejecutadas
    - Tiempo acumulado de queries
    - Endpoint y método HTTP
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Threshold en segundos (0.5 = 500ms)
        self.slow_request_threshold = getattr(settings, 'PERFORMANCE_LOG_THRESHOLD', 0.5)
        # Solo activo en DEBUG o si se configura explícitamente
        self.enabled = getattr(settings, 'PERFORMANCE_LOGGING_ENABLED', settings.DEBUG)
    
    def __call__(self, request):
        # Solo procesar endpoints de API
        if not self.enabled or not request.path.startswith('/api/'):
            return self.get_response(request)
        
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        # Procesar request
        response = self.get_response(request)
        
        # Calcular métricas
        duration = time.time() - start_time
        queries_count = len(connection.queries) - initial_queries
        queries_time = sum(float(q['time']) for q in connection.queries[initial_queries:]) if connection.queries else 0
        
        # Log solo si es lento o en DEBUG
        if duration > self.slow_request_threshold or settings.DEBUG:
            logger.info(
                f"PERF: {request.method} {request.path} | "
                f"Time: {duration:.3f}s | "
                f"Queries: {queries_count} ({queries_time:.3f}s) | "
                f"Status: {response.status_code}"
            )
        
        return response

