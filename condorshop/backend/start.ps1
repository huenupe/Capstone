#!/usr/bin/env pwsh
# Start Backend Server

Set-Location $PSScriptRoot

Write-Host "Starting CondorShop Backend..." -ForegroundColor Green

# Activate virtual environment and run server
& ".\venv\Scripts\python.exe" manage.py runserver



