from django.core.management.base import BaseCommand
from apps.orders.models import OrderStatus, PaymentStatus
from apps.products.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos iniciales: estados de orden, estados de pago, categorías y admin inicial'

    def handle(self, *args, **options):
        # Estados de orden
        order_statuses = [
            ('PENDING', 'Pendiente de pago'),
            ('PAID', 'Pago confirmado'),
            ('FAILED', 'Pago fallido'),
            ('CANCELLED', 'Cancelado'),
            ('PREPARING', 'En preparación'),
            ('SHIPPED', 'Enviado'),
            ('DELIVERED', 'Entregado'),
        ]
        
        for code, description in order_statuses:
            OrderStatus.objects.get_or_create(
                code=code,
                defaults={'description': description}
            )
            self.stdout.write(self.style.SUCCESS(f'Estado de orden creado: {code}'))

        # Estados de pago
        payment_statuses = [
            ('CREATED', 'Creado'),
            ('AUTHORIZED', 'Autorizado'),
            ('CAPTURED', 'Confirmado'),
            ('FAILED', 'Fallido'),
            ('REFUNDED', 'Reembolsado'),
        ]
        
        for code, description in payment_statuses:
            PaymentStatus.objects.get_or_create(
                code=code,
                defaults={'description': description}
            )
            self.stdout.write(self.style.SUCCESS(f'Estado de pago creado: {code}'))

        # Categorías ejemplo
        categories = [
            ('Tecnología', 'tecnologia', 'Productos tecnológicos'),
            ('Moda', 'moda', 'Ropa y accesorios'),
            ('Hogar', 'hogar', 'Artículos para el hogar'),
        ]
        
        for name, slug, description in categories:
            Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': description}
            )
            self.stdout.write(self.style.SUCCESS(f'Categoría creada: {name}'))

        # Usuario admin inicial (si no existe)
        admin_email = 'admin@condorshop.cl'
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.create_user(
                email=admin_email,
                password='admin123',  # Cambiar después
                first_name='Admin',
                last_name='Sistema',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Usuario admin creado: {admin_email} (contraseña: admin123)'))
        else:
            self.stdout.write(self.style.WARNING(f'Usuario admin ya existe: {admin_email}'))

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente'))

