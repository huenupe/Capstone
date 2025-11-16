from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import apps.products.signals  # noqa

