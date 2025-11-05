import secrets
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django_ratelimit.decorators import ratelimit
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from .models import PasswordResetToken

# Importar token blacklist solo si está disponible
try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    TOKEN_BLACKLIST_AVAILABLE = True
except ImportError:
    TOKEN_BLACKLIST_AVAILABLE = False

User = get_user_model()


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
@ratelimit(key='ip', rate='3/h', method='POST')
def forgot_password(request):
    """
    Solicitar recuperación de contraseña
    POST /api/auth/password-reset
    Body: { "email": "..." }
    Siempre retorna 204 (no revelar si email existe)
    """
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'El email es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email, is_active=True)
        
        # Generar token seguro
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=1)
        
        # Invalidar tokens anteriores del usuario
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
        
        # Crear nuevo token
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Construir URL de reset (frontend URL desde settings o request)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        # Enviar email
        try:
            send_mail(
                subject='Recuperación de contraseña - CondorShop',
                message=f'''
Hola {user.first_name or user.email},

Has solicitado restablecer tu contraseña en CondorShop.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, puedes ignorar este mensaje.

Saludos,
Equipo CondorShop
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error pero no fallar (para no revelar si email existe)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error sending password reset email: {e}')
        
        # Registrar en auditoría
        try:
            from apps.audit.models import AuditLog
            AuditLog.objects.create(
                action='PASSWORD_RESET_REQUESTED',
                user=user,
                details=f'Password reset requested for {user.email}'
            )
        except Exception:
            pass  # No fallar si auditoría no está disponible
        
    except User.DoesNotExist:
        # No hacer nada, pero no revelar que el email no existe
        pass
    
    # Siempre retornar 204 (éxito) para no revelar si email existe
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST')
def reset_password(request):
    """
    Confirmar recuperación de contraseña con token
    POST /api/auth/password-reset/confirm
    Body: { "token": "...", "new_password": "..." }
    """
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response(
            {'error': 'Token y nueva contraseña son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar token
    if not reset_token.is_valid():
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar contraseña
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    try:
        validate_password(new_password, reset_token.user)
    except ValidationError as e:
        return Response(
            {'error': '; '.join(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Actualizar contraseña
    user = reset_token.user
    user.set_password(new_password)
    user.save()
    
    # Marcar token como usado
    reset_token.used = True
    reset_token.save()
    
    # Invalidar todos los tokens JWT del usuario
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
            action='PASSWORD_RESET_COMPLETED',
            user=user,
            details=f'Password reset completed for {user.email}'
        )
    except Exception:
        pass
    
    return Response(status=status.HTTP_204_NO_CONTENT)


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

