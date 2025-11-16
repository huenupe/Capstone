"""
Tests para ProductPriceHistory - Acción 4
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from apps.products.models import Product, ProductPriceHistory, Category
from tests.factories import ProductFactory, CategoryFactory


@pytest.mark.django_db
class TestProductPriceHistoryModel:
    """Tests del modelo ProductPriceHistory"""
    
    def test_create_price_history(self):
        """Verificar que se puede crear un registro de historial"""
        category = CategoryFactory()
        product = ProductFactory(category=category, price=10000)
        
        history = ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            discount_price=None,
            discount_amount=None,
            discount_percent=None,
            final_price=product.final_price,
            effective_from=timezone.now(),
            effective_to=None
        )
        
        assert history.product == product
        assert history.price == 10000
        assert history.final_price == 10000
        assert history.is_current is True
        assert history.effective_to is None
    
    def test_price_history_with_discount(self):
        """Verificar historial con descuento"""
        category = CategoryFactory()
        product = ProductFactory(
            category=category,
            price=10000,
            discount_percent=20
        )
        
        history = ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            discount_price=None,
            discount_amount=None,
            discount_percent=20,
            final_price=product.final_price,
            effective_from=timezone.now(),
            effective_to=None
        )
        
        assert history.discount_percent == 20
        assert history.final_price == 8000  # 10000 - 20%
        assert history.is_current is True
    
    def test_is_current_property(self):
        """Verificar propiedad is_current"""
        category = CategoryFactory()
        product = ProductFactory(category=category)
        
        # Precio actual (effective_to es None)
        current = ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            final_price=product.final_price,
            effective_from=timezone.now(),
            effective_to=None
        )
        assert current.is_current is True
        
        # Precio pasado (effective_to tiene valor)
        past = ProductPriceHistory.objects.create(
            product=product,
            price=product.price - 1000,
            final_price=product.final_price - 1000,
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=timezone.now() - timedelta(days=5)
        )
        assert past.is_current is False
    
    def test_duration_days_property(self):
        """Verificar cálculo de duración en días"""
        category = CategoryFactory()
        product = ProductFactory(category=category)
        
        # Precio con fecha de fin
        past_date = timezone.now() - timedelta(days=10)
        end_date = timezone.now() - timedelta(days=5)
        
        history = ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            final_price=product.final_price,
            effective_from=past_date,
            effective_to=end_date
        )
        
        assert history.duration_days == 5
        
        # Precio actual (sin fecha de fin)
        current = ProductPriceHistory.objects.create(
            product=product,
            price=product.price,
            final_price=product.final_price,
            effective_from=timezone.now() - timedelta(days=3),
            effective_to=None
        )
        
        # Debe ser aproximadamente 3 días (puede variar por segundos)
        assert current.duration_days >= 2
        assert current.duration_days <= 4


@pytest.mark.django_db
class TestProductPriceHistorySignals:
    """Tests de signals que crean historial automáticamente"""
    
    def test_new_product_creates_initial_history(self):
        """Verificar que un producto nuevo crea registro inicial de historial"""
        category = CategoryFactory()
        
        # Crear producto nuevo
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="TEST-001",
            price=15000,
            category=category,
            stock_qty=10,
            active=True
        )
        
        # Verificar que se creó el historial
        history_count = ProductPriceHistory.objects.filter(product=product).count()
        assert history_count == 1, f"Se esperaba 1 registro de historial, se encontraron {history_count}"
        
        history = ProductPriceHistory.objects.get(product=product)
        assert history.price == 15000
        assert history.final_price == 15000
        assert history.is_current is True
        assert history.effective_to is None
    
    def test_price_change_creates_new_history(self):
        """Verificar que cambiar el precio crea nuevo registro de historial"""
        category = CategoryFactory()
        product = ProductFactory(category=category, price=10000)
        
        # Verificar historial inicial
        initial_count = ProductPriceHistory.objects.filter(product=product).count()
        assert initial_count == 1
        
        # Cambiar precio
        product.price = 12000
        product.save()
        
        # Verificar que se creó nuevo registro
        new_count = ProductPriceHistory.objects.filter(product=product).count()
        assert new_count == 2, f"Se esperaban 2 registros, se encontraron {new_count}"
        
        # Verificar que el registro anterior se cerró
        old_history = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=False
        ).first()
        assert old_history is not None
        assert old_history.effective_to is not None
        
        # Verificar que el nuevo registro es el actual
        current_history = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=True
        ).first()
        assert current_history is not None
        assert current_history.price == 12000
        assert current_history.is_current is True
    
    def test_discount_change_creates_new_history(self):
        """Verificar que cambiar descuento crea nuevo registro"""
        category = CategoryFactory()
        product = ProductFactory(category=category, price=10000, discount_percent=10)
        
        initial_count = ProductPriceHistory.objects.filter(product=product).count()
        
        # Cambiar descuento
        product.discount_percent = 20
        product.save()
        
        new_count = ProductPriceHistory.objects.filter(product=product).count()
        assert new_count == initial_count + 1
        
        # Verificar nuevo registro
        current = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=True
        ).first()
        assert current.discount_percent == 20
        assert current.final_price == 8000  # 10000 - 20%
    
    def test_multiple_price_changes(self):
        """Verificar múltiples cambios de precio"""
        category = CategoryFactory()
        product = ProductFactory(category=category, price=10000)
        
        # Primer cambio
        product.price = 11000
        product.save()
        
        # Segundo cambio
        product.price = 12000
        product.save()
        
        # Tercer cambio
        product.discount_percent = 15
        product.save()
        
        # Verificar que hay 4 registros (inicial + 3 cambios)
        total_count = ProductPriceHistory.objects.filter(product=product).count()
        assert total_count == 4
        
        # Verificar que solo hay un registro actual
        current_count = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=True
        ).count()
        assert current_count == 1
        
        # Verificar que hay 3 registros cerrados
        closed_count = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=False
        ).count()
        assert closed_count == 3


@pytest.mark.django_db
class TestProductPriceHistoryQueries:
    """Tests de consultas y relaciones"""
    
    def test_price_history_relationship(self):
        """Verificar relación inversa product.price_history"""
        category = CategoryFactory()
        product = ProductFactory(category=category)
        
        # ProductFactory ya crea un registro inicial (por signal)
        initial_count = product.price_history.count()
        assert initial_count == 1
        
        # Crear múltiples registros de historial adicionales
        ProductPriceHistory.objects.create(
            product=product,
            price=10000,
            final_price=10000,
            effective_from=timezone.now() - timedelta(days=10),
            effective_to=timezone.now() - timedelta(days=5)
        )
        ProductPriceHistory.objects.create(
            product=product,
            price=11000,
            final_price=11000,
            effective_from=timezone.now() - timedelta(days=5),
            effective_to=None
        )
        
        # Verificar acceso desde producto (inicial + 2 nuevos = 3)
        history = product.price_history.all()
        assert history.count() == 3
        
        # Verificar ordenamiento (más reciente primero)
        # El más reciente debería ser el actual (11000 o el inicial)
        assert history[0].price in [11000, product.price]
    
    def test_get_current_price_history(self):
        """Verificar obtención de precio actual"""
        category = CategoryFactory()
        product = ProductFactory(category=category)
        
        # Crear historial con precio actual
        current = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=True
        ).first()
        
        assert current is not None
        assert current.is_current is True
        assert current.price == product.price


@pytest.mark.django_db
class TestProductPriceHistoryAdmin:
    """Tests relacionados con el admin"""
    
    def test_price_history_inline_readonly(self):
        """Verificar que el historial en admin es de solo lectura"""
        from django.contrib import admin
        from apps.products.admin import ProductPriceHistoryInline
        
        # Crear inline con admin_site correcto
        inline = ProductPriceHistoryInline(Product, admin.site)
        
        # Verificar que no se puede agregar
        assert inline.has_add_permission(None) is False
        
        # Verificar que no se puede eliminar
        assert inline.can_delete is False


@pytest.mark.django_db
class TestProductPriceHistoryAPI:
    """Tests del endpoint API opcional"""
    
    def test_price_history_endpoint_exists(self):
        """Verificar que el endpoint existe en ProductViewSet"""
        from apps.products.views import ProductViewSet
        
        # Verificar que tiene el action
        assert hasattr(ProductViewSet, 'price_history')
    
    def test_price_history_serializer(self):
        """Verificar que el serializer funciona correctamente"""
        from apps.products.serializers import ProductPriceHistorySerializer
        
        category = CategoryFactory()
        product = ProductFactory(category=category, price=10000)
        
        history = ProductPriceHistory.objects.filter(
            product=product,
            effective_to__isnull=True
        ).first()
        
        serializer = ProductPriceHistorySerializer(history)
        data = serializer.data
        
        assert 'product' in data
        assert 'product_name' in data
        assert 'product_sku' in data
        assert 'price' in data
        assert 'final_price' in data
        assert 'price_formatted' in data
        assert 'final_price_formatted' in data
        assert 'discount_info' in data
        assert 'is_current' in data
        assert 'duration_days' in data
        assert data['is_current'] is True

