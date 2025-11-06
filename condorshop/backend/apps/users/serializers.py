from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User, Address


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password', 'password_confirm')
        extra_kwargs = {
            'phone': {'required': False, 'allow_blank': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Las contraseñas no coinciden"
            })
        return attrs
    
    def validate_password(self, value):
        """Validar contraseña con mensajes más claros"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            # Convertir errores de validación a mensajes más amigables
            error_messages = []
            for error in e.messages:
                error_str = str(error).lower()
                if 'too short' in error_str or 'muy corta' in error_str or 'al menos' in error_str:
                    error_messages.append('La contraseña debe tener al menos 8 caracteres')
                elif 'too common' in error_str or 'muy común' in error_str:
                    error_messages.append('Esta contraseña es muy común. Elige una más segura')
                elif 'too similar' in error_str or 'muy similar' in error_str:
                    error_messages.append('La contraseña es muy similar a tu información personal')
                elif 'entirely numeric' in error_str or 'enteramente numérica' in error_str:
                    error_messages.append('La contraseña no puede ser completamente numérica')
                else:
                    error_messages.append(str(error))
            raise serializers.ValidationError(error_messages[0] if len(error_messages) == 1 else error_messages)
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        try:
            user = User.objects.create_user(
                password=password,
                role='cliente',
                **validated_data
            )
            return user
        except Exception as e:
            # Capturar errores de creación (ej: email duplicado)
            error_msg = str(e)
            if 'email' in error_msg.lower() or 'duplicate' in error_msg.lower():
                raise serializers.ValidationError({
                    'email': 'Este correo electrónico ya está registrado'
                })
            raise serializers.ValidationError({
                'error': f'Error al crear usuario: {error_msg}'
            })


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 
                  'street', 'city', 'region', 'postal_code', 'role')
        read_only_fields = ('id', 'email', 'role')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AddressSerializer(serializers.ModelSerializer):
    """Serializer para direcciones guardadas"""
    class Meta:
        model = Address
        fields = ('id', 'label', 'street', 'number', 'apartment', 'city', 'region', 'postal_code', 'is_default', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Validar que solo haya una dirección por defecto"""
        if attrs.get('is_default') and self.instance:
            # Si se marca como default, quitar default de otras direcciones
            Address.objects.filter(user=self.instance.user, is_default=True).exclude(id=self.instance.id).update(is_default=False)
        return attrs


class AddressCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear direcciones"""
    label = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    number = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    apartment = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    postal_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    street = serializers.CharField(max_length=200)
    city = serializers.CharField(max_length=100)
    region = serializers.CharField(max_length=100)
    is_default = serializers.BooleanField(required=False, default=False)
    
    class Meta:
        model = Address
        fields = ('label', 'street', 'number', 'apartment', 'city', 'region', 'postal_code', 'is_default')
    
    def validate(self, attrs):
        # Convertir strings vacíos a None para campos opcionales
        if attrs.get('label') == '':
            attrs['label'] = None
        if attrs.get('number') == '':
            attrs['number'] = None
        if attrs.get('apartment') == '':
            attrs['apartment'] = None
        if attrs.get('postal_code') == '':
            attrs['postal_code'] = None
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'role')

