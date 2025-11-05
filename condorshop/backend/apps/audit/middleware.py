import json
from .models import AuditLog


class AuditMiddleware:
    """
    Middleware para registrar acciones de auditoría
    Registra visualizaciones y actualizaciones relevantes
    """
    EXCLUDED_PATHS = ['/admin/', '/static/', '/media/', '/api/auth/login', '/api/auth/register']
    TRACKED_ACTIONS = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']
    TRACKED_TABLES = {
        '/api/users/profile': 'users',
        '/api/admin/products': 'products',
        '/api/admin/orders': 'orders',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar request
        response = self.get_response(request)
        
        # Registrar auditoría si corresponde
        if self.should_log(request, response):
            self.log_action(request, response)
        
        return response

    def should_log(self, request, response):
        """Determina si se debe registrar la acción"""
        # Excluir ciertos paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return False
        
        # Solo métodos relevantes
        if request.method not in self.TRACKED_ACTIONS:
            return False
        
        # Solo respuestas exitosas
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        return True

    def log_action(self, request, response):
        """Registra la acción en audit_logs"""
        action = self.get_action_name(request.method, request.path)
        table_name = self.get_table_name(request.path)
        
        if not table_name:
            return
        
        try:
            # Obtener valores nuevos si hay body
            new_values = None
            if request.body and request.method in ['POST', 'PATCH', 'PUT']:
                try:
                    new_values = json.loads(request.body.decode('utf-8'))
                except:
                    pass
            
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action=action,
                table_name=table_name,
                record_id=self.get_record_id(request, response),
                new_values=new_values,
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            # No fallar la request si hay error en auditoría
            pass

    def get_action_name(self, method, path):
        """Determina el nombre de la acción"""
        if method == 'GET':
            return 'VIEW'
        elif method == 'POST':
            if 'create' in path or 'add' in path:
                return 'CREATE'
            return 'UPDATE'
        elif method in ['PATCH', 'PUT']:
            return 'UPDATE'
        elif method == 'DELETE':
            return 'DELETE'
        return 'UNKNOWN'

    def get_table_name(self, path):
        """Determina el nombre de la tabla desde el path"""
        # Mapeo directo
        for url_path, table in self.TRACKED_TABLES.items():
            if url_path in path:
                return table
        
        # Inferir desde path
        if '/products' in path:
            return 'products'
        elif '/orders' in path:
            return 'orders'
        elif '/users' in path:
            return 'users'
        elif '/cart' in path:
            return 'carts'
        return None

    def get_record_id(self, request, response):
        """Intenta obtener el ID del registro desde la respuesta"""
        try:
            if hasattr(response, 'data') and isinstance(response.data, dict):
                return response.data.get('id')
        except:
            pass
        return None

    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

