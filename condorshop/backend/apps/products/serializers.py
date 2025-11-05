from rest_framework import serializers
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ('id', 'url', 'image', 'alt_text', 'position')
    
    def get_image(self, obj):
        """Retorna URL absoluta de la imagen"""
        if not obj.url:
            return None
        
        # Si ya es URL absoluta, retornar tal cual
        if obj.url.startswith('http://') or obj.url.startswith('https://'):
            return obj.url
        
        # Si es ruta relativa, construir URL absoluta
        if obj.url.startswith('/media/'):
            # Construir URL absoluta usando el request del contexto
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.url)
            # Fallback: construir URL manualmente
            return f'http://localhost:8000{obj.url}'
        
        # Si es formato incorrecto, intentar convertir
        # Esto maneja casos donde la URL aún no está corregida
        if 'productos' in obj.url.lower():
            # Extraer nombre del archivo
            import re
            match = re.search(r'([^/\\]+\.(webp|jpg|jpeg|png|gif))', obj.url, re.IGNORECASE)
            if match:
                filename = match.group(1).lower().replace(' ', '-')
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(f'/media/productos/{filename}')
                return f'http://localhost:8000/media/productos/{filename}'
        
        return obj.url


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer para listado de productos (campos básicos)"""
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'discount_price', 'final_price', 'discount_percent', 
                  'has_discount', 'stock_qty', 'slug', 'main_image', 'category')
    
    def get_final_price(self, obj):
        """Retorna final_price como entero"""
        return int(obj.final_price)
    
    def get_discount_percent(self, obj):
        """Retorna el porcentaje de descuento calculado (entero)"""
        return int(obj.calculated_discount_percent)

    def get_main_image(self, obj):
        """Retorna la primera imagen ordenada por position con URL absoluta"""
        main_img = obj.images.order_by('position').first()
        if main_img:
            # Construir URL absoluta
            if main_img.url.startswith('/media/'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(main_img.url)
                return f'http://localhost:8000{main_img.url}'
            return main_img.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de producto con imágenes ordenadas"""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'discount_price', 
                  'final_price', 'discount_percent', 'has_discount', 'stock_qty', 
                  'brand', 'sku', 'category', 'images', 'created_at', 'updated_at')
    
    def get_final_price(self, obj):
        """Retorna final_price como entero"""
        return int(obj.final_price)
    
    def get_discount_percent(self, obj):
        """Retorna el porcentaje de descuento calculado (entero)"""
        return int(obj.calculated_discount_percent)


class ProductAdminSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de productos en admin"""
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.ReadOnlyField()
    calculated_discount_percent = serializers.SerializerMethodField()
    
    # Campos de descuento con validaciones estrictas (enteros)
    discount_price = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    discount_amount = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    discount_percent_field = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=100, source='discount_percent')

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'discount_price', 'discount_amount', 
                  'discount_percent_field', 'discount_percent', 'final_price', 'calculated_discount_percent', 'has_discount', 
                  'stock_qty', 'brand', 'sku', 'active', 'category', 'category_id', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'has_discount')
    
    def get_final_price(self, obj):
        """Retorna final_price como entero"""
        return int(obj.final_price)
    
    def get_calculated_discount_percent(self, obj):
        """Retorna el porcentaje calculado como entero"""
        return int(obj.calculated_discount_percent)
    
    def get_discount_percent(self, obj):
        """Retorna el porcentaje de descuento calculado (entero)"""
        return int(obj.calculated_discount_percent)
    
    def validate_discount_percent_field(self, value):
        """Validar que discount_percent sea entero 1-100"""
        if value is not None:
            if not isinstance(value, int):
                raise serializers.ValidationError('El porcentaje de descuento debe ser un número entero entre 1 y 100.')
            if value < 1 or value > 100:
                raise serializers.ValidationError('El porcentaje de descuento debe estar entre 1 y 100.')
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

