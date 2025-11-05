# Corrección de URLs de Imágenes - Instrucciones

## Problema Identificado

Las URLs de imágenes en la base de datos están mal formateadas:
- `file:///C:/Users/huenu/Desktop/condorshop/productos/...` (rutas absolutas de archivo)
- `backend\media\productos\...` (rutas relativas con backslashes)

Estas URLs no son accesibles desde el navegador. Necesitan ser rutas relativas como `/media/productos/...` que Django puede servir.

## Solución Implementada

### 1. Script de Corrección de URLs

Se creó un comando de Django para corregir automáticamente las URLs:

```bash
cd backend
python manage.py fix_image_urls
```

Este script:
- Convierte URLs `file:///C:/...` a `/media/productos/nombre-archivo.webp`
- Convierte URLs `backend\media\productos\...` a `/media/productos/nombre-archivo.webp`
- Normaliza nombres de archivo (minúsculas, sin espacios)

### 2. Serializers Actualizados

Los serializers ahora:
- Construyen URLs absolutas automáticamente (ej: `http://localhost:8000/media/productos/...`)
- Manejan tanto URLs corregidas como incorrectas (fallback)
- Agregan campo `image` además de `url` para compatibilidad con frontend

### 3. Frontend Actualizado

El frontend ahora:
- Usa función helper `getProductImage()` para obtener imágenes correctamente
- Maneja tanto `main_image` (lista) como `images[0].image` (detalle)
- Funciona con URLs absolutas del backend

## Pasos para Resolver el Problema

### Paso 1: Ejecutar el Script de Corrección

```bash
cd backend
python manage.py fix_image_urls
```

Verás un output como:
```
✓ Imagen ID 1: "file:///C:/Users/..." → "/media/productos/mouse-gamer-7200-dpi.webp"
✓ Imagen ID 2: "file:///C:/Users/..." → "/media/productos/smartwatch-sport.webp"
...
✅ Proceso completado: 5 URLs corregidas
```

### Paso 2: Verificar que Django Sirve Archivos Media

Asegúrate de que en `backend/condorshop_api/urls.py` esté:

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Esto ya está implementado, así que debería funcionar automáticamente.

### Paso 3: Verificar que las Imágenes Existen

Las imágenes deben estar en:
```
backend/media/productos/
```

Nombres de archivo esperados (normalizados):
- `mouse-gamer-7200-dpi.webp`
- `smartwatch-sport.webp`
- `teclado-mecánico-rgb.webp`
- `audífonos-bluetooth-tws.webp`
- `freidora-de-aire-4l.webp`

### Paso 4: Probar en el Frontend

1. Inicia el backend: `python manage.py runserver`
2. Inicia el frontend: `npm run dev`
3. Visita `http://localhost:5173`
4. Las imágenes deberían aparecer correctamente

## Verificación

### Ver URLs en la Base de Datos

```sql
SELECT id, url, product_id FROM product_images;
```

Deberías ver URLs como:
```
/media/productos/mouse-gamer-7200-dpi.webp
/media/productos/smartwatch-sport.webp
...
```

### Probar URLs Directamente

Abre en el navegador:
- `http://localhost:8000/media/productos/mouse-gamer-7200-dpi.webp`

Si la imagen carga, está funcionando correctamente.

## Notas Importantes

1. **Nombres de Archivo**: El script normaliza nombres (minúsculas, sin espacios). Si tus archivos tienen nombres diferentes, ajusta el script o renombra los archivos.

2. **Producción**: En producción, necesitarás configurar el servidor web (Nginx/Apache) para servir archivos estáticos/media. El script de corrección sigue siendo necesario.

3. **CORS**: Si las imágenes no cargan desde el frontend, verifica que CORS esté configurado correctamente en el backend.

4. **Cache del Navegador**: Si las imágenes aún no aparecen después de corregir las URLs, limpia la cache del navegador (Ctrl+Shift+R o Cmd+Shift+R).

## Troubleshooting

### Las imágenes siguen sin aparecer

1. **Verifica que el script se ejecutó correctamente:**
   ```bash
   python manage.py fix_image_urls
   ```

2. **Verifica que Django está sirviendo media:**
   - Abre `http://localhost:8000/media/productos/mouse-gamer-7200-dpi.webp` en el navegador
   - Si no carga, revisa la configuración de `MEDIA_URL` y `MEDIA_ROOT` en `settings.py`

3. **Verifica que los archivos existen:**
   ```bash
   ls backend/media/productos/
   ```

4. **Revisa la consola del navegador:**
   - Abre DevTools (F12)
   - Ve a la pestaña Network
   - Intenta cargar una página con productos
   - Verifica qué URLs se están solicitando y si hay errores 404

### URLs no se corrigen correctamente

Si el script no puede extraer el nombre del archivo de alguna URL, la dejará sin cambios y mostrará un warning. En ese caso, puedes corregir manualmente:

```sql
UPDATE product_images 
SET url = '/media/productos/nombre-archivo.webp' 
WHERE id = X;
```

## Cambios Realizados

### Backend
- ✅ `apps/products/management/commands/fix_image_urls.py` - Script de corrección
- ✅ `apps/products/serializers.py` - URLs absolutas y campo `image`
- ✅ `apps/products/views.py` - Contexto de request para serializers

### Frontend
- ✅ `src/utils/getProductImage.js` - Helper para obtener imágenes
- ✅ `src/components/products/ProductCard.jsx` - Usa helper
- ✅ `src/components/home/ProductRail.jsx` - Usa helper
- ✅ `src/pages/CategoryPage.jsx` - Usa helper
- ✅ `src/pages/Cart.jsx` - Usa helper
- ✅ `src/pages/Checkout/StepReview.jsx` - Usa helper
- ✅ `src/pages/Orders.jsx` - Usa helper

---

**Fecha:** 2025-01-27  
**Estado:** ✅ Implementado y listo para usar

