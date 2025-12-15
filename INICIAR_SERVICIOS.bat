@echo off
REM Script para iniciar todos los servicios de Evalyze-2025

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║           🚀 INICIAR EVALYZE - TODOS LOS SERVICIOS            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

set EVALYZE_DIR=c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025

echo ✅ Verificando rutas...
if not exist "%EVALYZE_DIR%\ai-service" (
    echo ❌ No encontrado: ai-service
    exit /b 1
)
if not exist "%EVALYZE_DIR%\django-docker" (
    echo ❌ No encontrado: django-docker
    exit /b 1
)
if not exist "%EVALYZE_DIR%\Eva-Front" (
    echo ❌ No encontrado: Eva-Front
    exit /b 1
)
echo ✅ Rutas verificadas

echo.
echo 📋 SERVICIOS A INICIAR:
echo   1. Ollama (LLM)            - http://localhost:11434
echo   2. AI Service              - http://localhost:8001
echo   3. Django Backend          - http://localhost:8000
echo   4. Angular Frontend        - http://localhost:4200
echo.
echo ⏳ Instrucciones:
echo   - Se abrirán 4 ventanas de terminal
echo   - MANTÉN TODAS ABIERTAS durante la sesión
echo   - Cierra las ventanas para detener los servicios
echo.

REM Solicitar confirmación
set /p confirm="¿Proceder con la inicialización? (S/N): "
if /i not "%confirm%"=="S" (
    echo Cancelado.
    exit /b 0
)

echo.
echo 🔄 Iniciando servicios...
echo.

REM Terminal 1: Ollama
echo ✅ Iniciando Ollama (LLM)
start "Ollama - LLM" cmd /k "echo Asegúrate de tener Ollama instalado en tu sistema. && echo Visitando: https://ollama.ai/ && echo. && echo Una vez instalado, ejecuta: ollama serve && pause"

REM Esperar a que Ollama esté listo
echo ⏳ Esperando 5 segundos para que Ollama se inicie...
timeout /t 5 /nobreak

REM Terminal 2: AI Service
echo ✅ Iniciando AI Service
start "AI Service - Puerto 8001" cmd /k "cd /d "%EVALYZE_DIR%\ai-service" && python main.py"

REM Esperar a que AI Service esté listo
echo ⏳ Esperando 3 segundos para que AI Service se inicie...
timeout /t 3 /nobreak

REM Terminal 3: Django
echo ✅ Iniciando Django Backend
start "Django Backend - Puerto 8000" cmd /k "cd /d "%EVALYZE_DIR%\django-docker" && python manage.py runserver 0.0.0.0:8000"

REM Esperar a que Django esté listo
echo ⏳ Esperando 3 segundos para que Django se inicie...
timeout /t 3 /nobreak

REM Terminal 4: Frontend
echo ✅ Iniciando Angular Frontend
start "Angular Frontend - Puerto 4200" cmd /k "cd /d "%EVALYZE_DIR%\Eva-Front" && npm start"

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    ✨ SERVICIOS INICIADOS                       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🌐 URLS DISPONIBLES:
echo   • Frontend:     http://localhost:4200
echo   • Backend API:  http://localhost:8000/api
echo   • AI Service:   http://localhost:8001/docs
echo   • Ollama:       http://localhost:11434/api/tags
echo.
echo 📝 LOGS:
echo   - Ver terminal de cada servicio para los logs
echo   - Errores aparecerán en las respectivas ventanas
echo.
echo ⏱️  Los servicios tardan 10-30 segundos en estar listos
echo 📌 Mantén estas ventanas abiertas para que los servicios sigan corriendo
echo.
pause
