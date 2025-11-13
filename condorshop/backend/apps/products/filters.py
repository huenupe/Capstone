import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method='filter_category')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    active = django_filters.BooleanFilter(field_name='active')
    # Permitir prefijos sobre el nombre con formato name__istartswith
    class Meta:
        model = Product
        fields = {
            'name': ['istartswith'],
        }

    def filter_category(self, queryset, name, value):
        """
        Permitir filtrar por ID numérico o por slug de la categoría.
        """
        if value is None or value == '':
            return queryset
        # Si el valor es estrictamente numérico, usar category_id
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            return queryset.filter(category_id=int(value))

        # De lo contrario, filtrar por slug
        return queryset.filter(category__slug=value)

