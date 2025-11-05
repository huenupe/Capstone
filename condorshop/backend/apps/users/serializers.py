from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'role')

