import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(method='filter_by_category_tree')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    active = django_filters.BooleanFilter(field_name='active')
    # Permitir prefijos sobre el nombre con formato name__istartswith
    class Meta:
        model = Product
        fields = {
            'name': ['istartswith'],
            'category': ['exact'],
            'active': ['exact'],
        }

    def filter_by_category_tree(self, queryset, name, value):
        """
        Filtra productos por categoría incluyendo todas sus subcategorías.
        Si filtras por 'Electrónica', incluye productos de 'Laptops', 'Celulares', etc.
        """
        if value is None or value == '':
            return queryset
        
        try:
            category = Category.objects.get(id=value)
            # Obtener esta categoría + todos sus descendientes
            categories = [category] + category.get_descendants()
            category_ids = [cat.id for cat in categories]
            return queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()

