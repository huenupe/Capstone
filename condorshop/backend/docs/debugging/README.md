# 🔍 Scripts de Debugging

Esta carpeta contiene scripts de análisis y debugging para el proyecto CondorShop.

## Scripts Disponibles

### `analyze_payment_transactions.py`
Análisis exhaustivo de la tabla `payment_transactions`:
- Columnas en BD vs Modelo Django
- Índices y Foreign Keys
- Comparación modelo vs BD
- Estado de campos críticos

**Uso:**
```bash
# Desde condorshop/backend
python manage.py shell < docs/debugging/analyze_payment_transactions.py
```

### `inspect_payment_table.py`
Inspección rápida de la estructura de `payment_transactions`:
- Columnas actuales
- Índices
- Foreign Keys
- Muestra de datos

**Uso:**
```bash
# Desde condorshop/backend
python docs/debugging/inspect_payment_table.py
```

## Notas

- Estos scripts son herramientas de desarrollo/debugging
- No afectan el funcionamiento del proyecto
- Pueden ejecutarse en cualquier momento para análisis
- Útiles para debugging de migraciones y estructura de BD

---

**Última actualización**: 2025-11-14

