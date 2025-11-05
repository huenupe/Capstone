# Script para activar el venv sin problemas de política de ejecución
# Ejecuta: powershell -ExecutionPolicy Bypass -File .\activate_venv.ps1

$ErrorActionPreference = "Stop"

Write-Host "Activando entorno virtual..." -ForegroundColor Green
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

Write-Host "`nEntorno virtual activado!" -ForegroundColor Green
Write-Host "Puedes ejecutar ahora:" -ForegroundColor Yellow
Write-Host "  python manage.py migrate" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor Cyan
Write-Host ""





