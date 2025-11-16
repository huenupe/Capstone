"""
Management command para liberar reservas de stock expiradas.

Uso:
    python manage.py release_expired_reservations --minutes=30
    python manage.py release_expired_reservations --hours=1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from apps.products.models import InventoryMovement, Product


class Command(BaseCommand):
    help = 'Libera reservas de stock expiradas (órdenes pendientes que no se completaron)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Minutos de antigüedad para considerar una reserva como expirada (default: 30)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=None,
            help='Horas de antigüedad (alternativa a --minutes)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin hacer cambios reales'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        if options['hours']:
            minutes = options['hours'] * 60
        
        dry_run = options['dry_run']
        
        # Calcular fecha límite
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        self.stdout.write(f"Buscando reservas anteriores a {cutoff_time}")
        
        # Buscar movimientos de reserva sin referencia (órdenes que nunca se crearon)
        # o con referencia a órdenes que están en estado PENDING por mucho tiempo
        from apps.orders.models import Order, OrderStatus
        
        try:
            pending_status = OrderStatus.objects.get(code='PENDING')
        except OrderStatus.DoesNotExist:
            self.stdout.write(self.style.WARNING('Estado PENDING no encontrado'))
            return
        
        # Reservas sin referencia (fallaron al crear orden)
        orphan_reservations = InventoryMovement.objects.filter(
            movement_type='reserve',
            reference_id__isnull=True,
            created_at__lt=cutoff_time
        )
        
        # Reservas de órdenes PENDING antiguas
        old_pending_orders = Order.objects.filter(
            status=pending_status,
            created_at__lt=cutoff_time
        )
        
        total_released = 0
        
        with transaction.atomic():
            # Liberar reservas huérfanas
            for movement in orphan_reservations:
                product = movement.product
                quantity = movement.quantity_change
                
                if not dry_run:
                    product.release_stock(
                        quantity=quantity,
                        reason='Reservation expired (no order created)',
                        reference_id=movement.id
                    )
                
                total_released += quantity
                self.stdout.write(
                    f"{'[DRY-RUN] ' if dry_run else ''}Liberando {quantity} unidades de {product.name} "
                    f"(reserva huérfana del {movement.created_at})"
                )
            
            # Liberar reservas de órdenes PENDING antiguas
            for order in old_pending_orders:
                # Obtener movimientos de reserva para esta orden
                order_reservations = InventoryMovement.objects.filter(
                    movement_type='reserve',
                    reference_type='order',
                    reference_id=order.id,
                    created_at__lt=cutoff_time
                )
                
                for movement in order_reservations:
                    product = movement.product
                    quantity = movement.quantity_change
                    
                    if not dry_run:
                        product.release_stock(
                            quantity=quantity,
                            reason=f'Order {order.id} expired (pending too long)',
                            reference_id=order.id
                        )
                    
                    total_released += quantity
                    self.stdout.write(
                        f"{'[DRY-RUN] ' if dry_run else ''}Liberando {quantity} unidades de {product.name} "
                        f"(orden {order.id} pendiente desde {order.created_at})"
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY-RUN] Se liberarían {total_released} unidades de stock'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Liberadas {total_released} unidades de stock'
                )
            )

