#!/usr/bin/env python
"""
Script para verificar que transbank-sdk se puede importar correctamente
"""
import sys
import os

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop_api.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"Error configurando Django: {e}")
    sys.exit(1)

print("=" * 60)
print("VERIFICACIÓN DE TRANSBANK-SDK")
print("=" * 60)

# 1. Verificar importación directa
print("\n1. Verificando importación directa...")
try:
    from transbank.webpay.webpay_plus.transaction import Transaction
    from transbank.error.transbank_error import TransbankError
    print("   [OK] transbank-sdk se puede importar correctamente")
except ImportError as e:
    print(f"   [ERROR] No se puede importar transbank-sdk: {e}")
    print(f"   [SOLUCIÓN] Ejecuta: pip install transbank-sdk==3.0.0")
    sys.exit(1)

# 2. Verificar desde el servicio
print("\n2. Verificando desde apps.orders.services...")
try:
    from apps.orders.services import TRANSBANK_AVAILABLE, webpay_service
    print(f"   TRANSBANK_AVAILABLE: {TRANSBANK_AVAILABLE}")
    print(f"   webpay_service: {'OK' if webpay_service is not None else 'None'}")
    
    if not TRANSBANK_AVAILABLE:
        print("   [ERROR] TRANSBANK_AVAILABLE es False")
        sys.exit(1)
    
    if webpay_service is None:
        print("   [ERROR] webpay_service es None")
        sys.exit(1)
    
    print("   [OK] WebpayService está disponible")
except Exception as e:
    print(f"   [ERROR] Error al verificar servicio: {e}")
    sys.exit(1)

# 3. Verificar configuración
print("\n3. Verificando configuración...")
try:
    from django.conf import settings
    config = settings.WEBPAY_CONFIG
    print(f"   ENVIRONMENT: {config['ENVIRONMENT']}")
    print(f"   COMMERCE_CODE: {config['COMMERCE_CODE']}")
    print(f"   API_KEY: {'***' + config['API_KEY'][-4:] if config['API_KEY'] else 'NO CONFIGURADO'}")
    print(f"   RETURN_URL: {config['RETURN_URL']}")
    print(f"   FINAL_URL: {config['FINAL_URL']}")
    print("   [OK] Configuración correcta")
except Exception as e:
    print(f"   [ERROR] Error al verificar configuración: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] TODO CORRECTO - Webpay está listo para usar")
print("=" * 60)
print("\n[IMPORTANTE] Si el servidor Django está corriendo, REINÍCIALO:")
print("   1. Detén el servidor (Ctrl+C)")
print("   2. Inicia nuevamente: python manage.py runserver")
print("=" * 60)

