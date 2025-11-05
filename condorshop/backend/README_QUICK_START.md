# Inicio Rápido - CondorShop Backend

## ⚡ Comando Rápido para Levantar el Servidor

Desde el directorio raíz del proyecto:

```powershell
cd backend
python manage.py runserver
```

**¡Eso es todo!** El script `manage.py` automáticamente detectará y usará el entorno virtual local.

---

## 📋 Comandos Disponibles

### Levantar el servidor:
```powershell
cd backend
python manage.py runserver
```

### Ejecutar migraciones:
```powershell
cd backend
python manage.py migrate
```

### Crear superusuario:
```powershell
cd backend
python manage.py createsuperuser
```

### Cargar datos iniciales:
```powershell
cd backend
python manage.py load_initial_data
```

---

## 🎯 URLs Disponibles

- **API Root:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/
- **API Auth:** http://127.0.0.1:8000/api/auth/
- **API Products:** http://127.0.0.1:8000/api/products/

---

## ✅ Requisitos Previos

1. **Python 3.11+** instalado
2. **MySQL 8.0** en ejecución
3. **Base de datos `condorshop`** creada
4. **Archivo `.env`** configurado en `backend/.env`

### Primera Vez - Instalación:

```powershell
cd backend

# Crear entorno virtual (si no existe)
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# Configurar base de datos en .env
# Editar backend/.env con tus credenciales de MySQL

# Ejecutar migraciones (primera vez)
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

Después de la primera instalación, solo necesitas:
```powershell
cd backend
python manage.py runserver
```

---

## 🔧 Solución de Problemas

### Si aparece error "No module named 'django'":
Asegúrate de que las dependencias estén instaladas:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Si aparece error de política de ejecución en PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Si el servidor no inicia:
1. Verifica que MySQL esté en ejecución
2. Verifica las credenciales en `backend/.env`
3. Verifica que la base de datos `condorshop` exista

---

## 📝 Notas

- El entorno virtual (`venv`) ya viene con todas las dependencias instaladas
- No necesitas activar manualmente el venv si usas `python manage.py` directamente
- El servidor se ejecuta en http://127.0.0.1:8000/ por defecto

