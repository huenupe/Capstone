# Guía de Uso del Backend Django

## Problema con PowerShell Execution Policy

Si encuentras el error: "la ejecución de scripts está deshabilitada en este sistema", usa una de estas soluciones:

## Soluciones

### Opción 1: Usar scripts .bat (Más fácil)
Simplemente ejecuta los archivos `.bat` creados:

```cmd
run_both.bat        # Ejecuta migraciones y servidor
run_migrate.bat     # Solo migraciones
run_server.bat      # Solo servidor
```

### Opción 2: Usar Python directamente del venv
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

### Opción 3: Cambiar política de PowerShell (solo para esta sesión)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

### Opción 4: Ejecutar script PowerShell con bypass
```powershell
powershell -ExecutionPolicy Bypass -File activate_venv.ps1
```

## Configuración de Base de Datos

**IMPORTANTE:** Antes de ejecutar migraciones, actualiza la contraseña de MySQL en `backend/.env`:

```env
DB_PASSWORD=tu_password_real_aqui
```

## Comandos después de configurar la BD

Una vez actualizada la contraseña:

```powershell
# Opción más simple (usa .bat):
run_both.bat

# O manualmente con Python del venv:
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

El servidor estará disponible en: http://127.0.0.1:8000/





