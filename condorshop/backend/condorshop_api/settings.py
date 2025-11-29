"""
Django settings for condorshop_api project.
"""
import os
import mimetypes
import warnings
from pathlib import Path
import environ

# Suprimir RuntimeWarning sobre acceso a BD durante inicialización de apps
# (común cuando se importan signals en AppConfig.ready())
warnings.filterwarnings('ignore', category=RuntimeWarning, module='django.db.backends.utils')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Asegurar que los archivos .webp se sirvan con el tipo de contenido correcto en desarrollo
mimetypes.add_type("image/webp", ".webp", strict=True)

# Load environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

FRONTEND_RESET_URL = env('FRONTEND_RESET_URL', default='http://localhost:5173/reset-password')
PASSWORD_RESET_TIMEOUT_HOURS = env.int('PASSWORD_RESET_TIMEOUT_HOURS', default=1)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # Soporte para funcionalidades avanzadas de PostgreSQL
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    # Local apps
    'condorshop_api.apps.CondorShopAPIConfig',
    'apps.common',
    'apps.users',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'condorshop_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'condorshop_api.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
        # Optimizaciones para base de datos remota (Supabase)
        'CONN_MAX_AGE': 600,  # Reutilizar conexiones por 10 minutos (reduce latencia)
        'OPTIONS': {
            'connect_timeout': 10,  # Timeout de conexión en segundos
            'options': '-c statement_timeout=30000',  # Timeout de queries: 30 segundos
            'sslmode': 'require',  # Requerido para Supabase (conexiones SSL)
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # Reducido de 20 a 10 para mejorar LCP (menor carga inicial)
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=env.int('JWT_EXPIRATION_HOURS', default=24)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_DEFAULT_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
]
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=CORS_DEFAULT_ORIGINS
)
# Asegurar que los orígenes por defecto estén presentes, aunque .env no se actualice
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS + CORS_DEFAULT_ORIGINS))
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-token',  # Para carrito de invitados
]

# Exponer headers personalizados para que el frontend pueda leerlos
CORS_EXPOSE_HEADERS = [
    'X-Session-Token',
]

# CSRF Settings
CSRF_TRUSTED_ORIGINS_DEFAULT = CORS_DEFAULT_ORIGINS
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=CSRF_TRUSTED_ORIGINS_DEFAULT
)
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS + CSRF_TRUSTED_ORIGINS_DEFAULT))

# Security Settings (production-ready)
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

if DEBUG:
    # Sessions en desarrollo: expiran al cerrar navegador o tras 30 minutos de inactividad
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = env.int('DEV_SESSION_COOKIE_AGE', default=1800)

# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@condorshop.cl')

# Anymail settings (example with Mailgun)
if EMAIL_BACKEND == 'anymail.backends.mailgun.EmailBackend':
    ANYMAIL = {
        "MAILGUN_API_KEY": env('ANYMAIL_MAILGUN_API_KEY', default=''),
        "MAILGUN_SENDER_DOMAIN": env('ANYMAIL_MAILGUN_SENDER_DOMAIN', default='mg.example.com'),
    }

# ============================================
# WEBPAY PLUS CONFIGURATION
# ============================================
WEBPAY_CONFIG = {
    'ENVIRONMENT': env('WEBPAY_ENVIRONMENT', default='integration'),
    'COMMERCE_CODE': env('WEBPAY_COMMERCE_CODE', default='597055555532'),
    'API_KEY': env('WEBPAY_API_KEY', default='579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'),
    'RETURN_URL': env('WEBPAY_RETURN_URL', default='http://localhost:8000/api/payments/return/'),
    'FINAL_URL': env('WEBPAY_FINAL_URL', default='http://localhost:5173/payment/result'),
}

# Validar configuración en startup
if WEBPAY_CONFIG['ENVIRONMENT'] == 'production':
    from django.core.exceptions import ImproperlyConfigured
    required_webpay_vars = ['COMMERCE_CODE', 'API_KEY', 'RETURN_URL', 'FINAL_URL']
    for var in required_webpay_vars:
        if WEBPAY_CONFIG[var].startswith('http://localhost'):
            raise ImproperlyConfigured(
                f"Webpay en producción no puede usar localhost. Configura {var}"
            )

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Cache Configuration
# Configuración dual: LocMem para desarrollo, Redis para producción
# Mejora significativa el rendimiento de endpoints críticos (productos, categorías)
REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env.int('REDIS_PORT', default=6379)
REDIS_DB = env.int('REDIS_DB', default=0)
REDIS_PASSWORD = env('REDIS_PASSWORD', default=None)

if DEBUG:
    # Desarrollo: usar caché en memoria (no requiere Redis)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'condorshop-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,  # Eliminar 1/3 de entradas cuando se alcanza MAX_ENTRIES
            },
            'TIMEOUT': 300,  # 5 minutos por defecto
        }
    }
else:
    # Producción: usar Redis para mejor rendimiento y persistencia
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PASSWORD': REDIS_PASSWORD,
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,  # No fallar si Redis está caído
            },
            'KEY_PREFIX': 'condorshop',
            'TIMEOUT': 300,  # 5 minutos por defecto
        }
    }

