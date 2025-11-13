from django.core.exceptions import DisallowedHost
from rest_framework import serializers

from apps.common.utils import format_clp
from .models import Category, Product, ProductImage


def to_int(value):
    """Convertir Decimals u otras representaciones numéricas a enteros."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value_str = str(value)
    if not value_str:
        return None
    if '.' not in value_str:
        return int(value_str)
    integer_part, fractional_part = value_str.split('.', 1)
    fractional_part = (fractional_part + '00')[:2]
    rounded = int(integer_part or '0')
    if int(fractional_part) >= 50:
        rounded += 1
    return rounded


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image')

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        # obj.image.url ya incluye MEDIA_URL; _build_image_url se encarga de normalizar
        return _build_image_url(obj.image.url, request)


def _build_image_url(raw_url: str, request):
    """
    Normaliza la URL de imagen guardada en la base de datos y construye una URL absoluta.
    Maneja rutas con backslash (Windows), rutas relativas y URLs absolutas.
    """
    if not raw_url:
        return None

    url = str(raw_url).strip()
    url = url.replace('\\', '/')

    # URL absoluta ya válida
    if url.startswith('http://') or url.startswith('https://'):
        return url

    # Forzar prefijo / para rutas relativas dentro de media/static
    if not url.startswith('/'):
        url = f'/{url.lstrip("/")}'

    # Si apunta a media sin slash inicial, normalizar a /media/...
    if url.startswith('//'):
        url = f'/{url.lstrip("/")}'

    if request:
        try:
            return request.build_absolute_uri(url)
        except DisallowedHost:
            # Entornos de prueba pueden no tener el host en ALLOWED_HOSTS
            pass

    # Fallback para entornos sin request (tests, comandos)
    return f'http://localhost:8000{url}'


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ('id', 'url', 'image', 'alt_text', 'position')
    
    def get_image(self, obj):
        """Retorna URL absoluta de la imagen"""
        request = self.context.get('request')
        return _build_image_url(obj.url, request)


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer para listado de productos (campos básicos)"""
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    calculated_discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.BooleanField(read_only=True)
    price_formatted = serializers.SerializerMethodField()
    final_price_formatted = serializers.SerializerMethodField()
    discount_price_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'discount_price', 'final_price', 'discount_percent', 
                  'calculated_discount_percent', 'has_discount', 'stock_qty', 'slug', 'main_image', 'category',
                  'price_formatted', 'final_price_formatted', 'discount_price_formatted')

    def get_final_price(self, obj):
        return int(obj.final_price)

    def get_discount_percent(self, obj):
        return int(obj.calculated_discount_percent)

    def get_calculated_discount_percent(self, obj):
        return int(obj.calculated_discount_percent)

    def get_main_image(self, obj):
        """Retorna la primera imagen ordenada por position con URL absoluta"""
        main_img = obj.images.order_by('position').first()
        if not main_img:
            return None

        request = self.context.get('request')
        return _build_image_url(main_img.url, request)

    def get_price_formatted(self, obj):
        return format_clp(obj.price)

    def get_final_price_formatted(self, obj):
        return format_clp(obj.final_price)

    def get_discount_price_formatted(self, obj):
        if obj.discount_price:
            return format_clp(obj.discount_price)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de producto con imágenes ordenadas"""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    calculated_discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.BooleanField(read_only=True)
    price_formatted = serializers.SerializerMethodField()
    final_price_formatted = serializers.SerializerMethodField()
    discount_price_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'discount_price', 
                  'final_price', 'discount_percent', 'calculated_discount_percent', 'has_discount', 'stock_qty', 
                  'brand', 'sku', 'category', 'images', 'created_at', 'updated_at',
                  'price_formatted', 'final_price_formatted', 'discount_price_formatted')

    def get_final_price(self, obj):
        return int(obj.final_price)

    def get_discount_percent(self, obj):
        return int(obj.calculated_discount_percent)

    def get_calculated_discount_percent(self, obj):
        return int(obj.calculated_discount_percent)

    def get_price_formatted(self, obj):
        return format_clp(obj.price)

    def get_final_price_formatted(self, obj):
        return format_clp(obj.final_price)

    def get_discount_price_formatted(self, obj):
        if obj.discount_price:
            return format_clp(obj.discount_price)
        return None


class ProductAdminSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de productos en admin"""
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    final_price = serializers.IntegerField(source='final_price', read_only=True)
    discount_percent = serializers.IntegerField(source='calculated_discount_percent', read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    calculated_discount_percent = serializers.IntegerField(read_only=True)
    price_formatted = serializers.SerializerMethodField()
    final_price_formatted = serializers.SerializerMethodField()
    discount_price_formatted = serializers.SerializerMethodField()
    
    # Campos de descuento con validaciones estrictas (enteros)
    discount_price = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    discount_amount = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    discount_percent_field = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100, source='discount_percent')

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'discount_price', 'discount_amount', 
                  'discount_percent_field', 'discount_percent', 'final_price', 'calculated_discount_percent', 'has_discount', 
                  'stock_qty', 'brand', 'sku', 'active', 'category', 'category_id', 'created_at', 'updated_at',
                  'price_formatted', 'final_price_formatted', 'discount_price_formatted')
        read_only_fields = ('created_at', 'updated_at', 'has_discount')

    def validate_discount_percent_field(self, value):
        """Validar que discount_percent sea entero 0-100"""
        if value is not None:
            if not isinstance(value, int):
                raise serializers.ValidationError('El porcentaje de descuento debe ser un número entero entre 0 y 100.')
            if value < 0 or value > 100:
                raise serializers.ValidationError('El porcentaje de descuento debe estar entre 0 y 100.')
        return value
    
    def validate_discount_price(self, value):
        """Validar que discount_price sea entero"""
        if value is not None:
            if not isinstance(value, int):
                raise serializers.ValidationError('El precio final del descuento debe ser un número entero en pesos chilenos (CLP, sin decimales).')
            if value < 0:
                raise serializers.ValidationError('El precio final del descuento no puede ser negativo.')
        return value
    
    def validate_discount_amount(self, value):
        """Validar que discount_amount sea entero"""
        if value is not None:
            if not isinstance(value, int):
                raise serializers.ValidationError('El monto a descontar debe ser un número entero en pesos chilenos (CLP, sin decimales).')
            if value < 0:
                raise serializers.ValidationError('El monto a descontar no puede ser negativo.')
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas"""
        # Validar category_id primero
        if 'category_id' in attrs:
            category_id = attrs.pop('category_id')
            if category_id:
                from .models import Category
                try:
                    attrs['category'] = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    raise serializers.ValidationError({'category_id': 'Categoría no encontrada'})
        
        # Validaciones de descuentos
        price = attrs.get('price', self.instance.price if self.instance else None)
        discount_price = attrs.get('discount_price', self.instance.discount_price if self.instance else None)
        discount_amount = attrs.get('discount_amount', self.instance.discount_amount if self.instance else None)
        
        if price:
            price_int = int(price)
            
            if discount_price is not None and discount_price > price_int:
                raise serializers.ValidationError({
                    'discount_price': 'El precio final del descuento no puede ser mayor que el precio original.'
                })
            
            if discount_amount is not None and discount_amount > price_int:
                raise serializers.ValidationError({
                    'discount_amount': 'El monto a descontar no puede ser mayor que el precio original.'
                })
        
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['price'] = to_int(instance.price)
        data['final_price'] = to_int(instance.final_price)
        data['discount_price'] = to_int(instance.discount_price)
        data['discount_amount'] = to_int(instance.discount_amount)
        data['price_formatted'] = format_clp(instance.price)
        data['final_price_formatted'] = format_clp(instance.final_price)
        data['discount_price_formatted'] = format_clp(instance.discount_price) if instance.discount_price else None
        return data

