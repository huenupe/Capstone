import logging
import uuid
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django_ratelimit.decorators import ratelimit
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserProfileSerializer, AddressSerializer, AddressCreateSerializer
from .models import PasswordResetToken, Address

# Importar token blacklist solo si está disponible
try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    TOKEN_BLACKLIST_AVAILABLE = True
except ImportError:
    TOKEN_BLACKLIST_AVAILABLE = False

User = get_user_model()

FRONTEND_RESET_URL = getattr(settings, 'FRONTEND_RESET_URL', 'http://localhost:5173/reset-password')
PASSWORD_RESET_TIMEOUT_HOURS = getattr(settings, 'PASSWORD_RESET_TIMEOUT_HOURS', 1)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def register(request):
    """
    Registro de nuevos clientes
    POST /api/auth/register
    Body: { "email": "...", "first_name": "...", "last_name": "...", "password": "...", "password_confirm": "...", "phone": "..." (opcional) }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Capturar errores de creación de usuario (ej: email duplicado)
            return Response({
                'error': f'Error al crear usuario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Formatear errores para mejor legibilidad
    errors = {}
    for field, messages in serializer.errors.items():
        if isinstance(messages, list):
            errors[field] = messages[0] if len(messages) == 1 else messages
        else:
            errors[field] = messages
    
    return Response(errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def login(request):
    """
    Login de usuarios
    POST /api/auth/login
    Body: { "email": "...", "password": "..." }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email y contraseña son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.check_password(password):
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Usuario inactivo'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    return Response({
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        },
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Ver y editar perfil de usuario autenticado
    GET /api/users/profile
    PATCH /api/users/profile
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def forgot_password(request):
    """
    Solicitar recuperación de contraseña.
    POST /api/auth/forgot-password
    Body: { "email": "..." }
    Siempre retorna 200 sin revelar si el email existe.
    """
    email = request.data.get('email')

    if not email:
        return Response({'error': 'El email es requerido'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email, is_active=True).first()

    if user:
        # Invalidar tokens previos pendientes
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())

        # Crear nuevo token
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_url = f"{FRONTEND_RESET_URL}?token={reset_token.token}"

        message = (
            f"Hola {user.first_name or user.email},\n\n"
            "Recibimos una solicitud para restablecer tu contraseña en CondorShop.\n\n"
            f"Utiliza el siguiente enlace para crear una nueva contraseña (vigente por {PASSWORD_RESET_TIMEOUT_HOURS} hora(s)):\n"
            f"{reset_url}\n\n"
            "Si no solicitaste este cambio, puedes ignorar este mensaje.\n\n"
            "Saludos cordiales,\n"
            "Equipo CondorShop"
        )

        try:
            send_mail(
                subject='Recuperar contraseña - CondorShop',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("Error enviando correo de recuperación: %s", exc)

        # Registrar auditoría (best-effort)
        try:
            from apps.audit.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='PASSWORD_RESET_REQUEST',
                table_name='users',
                record_id=user.id,
                new_values={'email': user.email},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception:
            pass

    return Response(
        {'message': 'Si el email existe, recibirás instrucciones'},
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def addresses(request):
    """
    Listar y crear direcciones del usuario autenticado
    GET /api/users/addresses - Listar direcciones
    POST /api/users/addresses - Crear nueva dirección
    """
    if request.method == 'GET':
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = AddressCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Si se marca como default, quitar default de otras direcciones
            if serializer.validated_data.get('is_default'):
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            try:
                address = serializer.save(user=request.user)
                return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error creating address: {e}')
                return Response(
                    {'error': f'Error al crear la dirección: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def address_detail(request, address_id):
    """
    Ver, actualizar o eliminar una dirección específica
    GET /api/users/addresses/{id} - Ver dirección
    PATCH /api/users/addresses/{id} - Actualizar dirección
    DELETE /api/users/addresses/{id} - Eliminar dirección
    """
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return Response(
            {'error': 'Dirección no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            # Si se marca como default, quitar default de otras direcciones
            if serializer.validated_data.get('is_default'):
                Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def reset_password(request):
    """
    Restablecer contraseña usando un token válido.
    POST /api/auth/reset-password
    Body: { "token": "...", "password": "...", "password_confirm": "..." }
    """
    token_value = request.data.get('token')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')

    if not token_value or not password or not password_confirm:
        return Response(
            {'error': 'Token, contraseña y confirmación son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password_confirm:
        return Response(
            {'error': 'Las contraseñas no coinciden'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token_uuid = uuid.UUID(str(token_value))
    except (TypeError, ValueError):
        return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

    reset_token = PasswordResetToken.objects.select_related('user').filter(token=token_uuid).first()
    if not reset_token or not reset_token.is_valid():
        return Response({'error': 'Token inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

    user = reset_token.user

    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        return Response({'error': '; '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.save(update_fields=['password', 'updated_at'])

    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=['used_at'])

    # Invalidar otros tokens activos
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).exclude(id=reset_token.id).update(used_at=timezone.now())

    if TOKEN_BLACKLIST_AVAILABLE:
        try:
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for outstanding_token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
        except Exception:
            pass

    try:
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='PASSWORD_RESET_COMPLETED',
            table_name='users',
            record_id=user.id,
            new_values={'email': user.email},
            ip_address=request.META.get('REMOTE_ADDR')
        )
    except Exception:
        pass

    return Response({'message': 'Contraseña actualizada correctamente'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_reset_token(request, token):
    """
    Verificar si un token de recuperación es válido.
    GET /api/auth/verify-reset-token/<token>/
    """
    try:
        token_uuid = uuid.UUID(str(token))
    except (TypeError, ValueError):
        return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

    reset_token = PasswordResetToken.objects.filter(token=token_uuid).first()
    if not reset_token or not reset_token.is_valid():
        return Response({'error': 'Token inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'Token válido'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deactivate_account(request):
    """
    Desactivar cuenta de usuario (soft delete)
    DELETE /api/users/me
    """
    user = request.user
    
    # Soft delete
    user.is_active = False
    user.save()
    
    # Invalidar todos los tokens JWT
    if TOKEN_BLACKLIST_AVAILABLE:
        try:
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for outstanding_token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
        except Exception:
            pass
    
    # Registrar en auditoría
    try:
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            action='ACCOUNT_DEACTIVATED',
            user=user,
            details=f'Account deactivated for {user.email}'
        )
    except Exception:
        pass
    
    return Response(status=status.HTTP_204_NO_CONTENT)

