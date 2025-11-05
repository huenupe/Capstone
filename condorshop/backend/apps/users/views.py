from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserProfileSerializer

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

