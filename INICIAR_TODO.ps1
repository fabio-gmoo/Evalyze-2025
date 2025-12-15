# Script para iniciar todos los servicios de Evalyze
# Ejecutar con: powershell -ExecutionPolicy Bypass -File INICIAR_TODO.ps1

Clear-Host
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🚀 EVALYZE - INICIADOR AUTOMÁTICO DE SERVICIOS 🚀            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar Ollama
Write-Host "🔍 Verificando dependencias..." -ForegroundColor Yellow
$ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaExists) {
    Write-Host "❌ OLLAMA NO ESTÁ INSTALADO" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️  PASOS PARA INSTALAR OLLAMA:" -ForegroundColor Yellow
    Write-Host "   1. Abre: https://ollama.ai/" -ForegroundColor White
    Write-Host "   2. Descarga el instalador para Windows" -ForegroundColor White
    Write-Host "   3. Instala en tu computadora" -ForegroundColor White
    Write-Host "   4. Reinicia PowerShell" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter cuando hayas instalado Ollama"
    Write-Host ""
}

# Crear 4 ventanas PowerShell
Write-Host "📟 Abriendo 4 terminales para los servicios..." -ForegroundColor Cyan
Write-Host ""

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "C:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\.venv-1\Scripts\python.exe"
$nodeExe = "npm"

# Terminal 1: Ollama
Write-Host "📦 Terminal 1: OLLAMA (Ejecutando en nueva ventana...)" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"
Start-Sleep -Seconds 2

# Terminal 2: AI Service
Write-Host "🧠 Terminal 2: AI SERVICE (Ejecutando en nueva ventana...)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectPath\ai-service'; & '$pythonExe' main.py"
Start-Sleep -Seconds 2

# Terminal 3: Django
Write-Host "🐍 Terminal 3: DJANGO (Ejecutando en nueva ventana...)" -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectPath\django-docker'; & '$pythonExe' manage.py migrate 2>&1 | Out-Null; & '$pythonExe' manage.py runserver"
Start-Sleep -Seconds 2

# Terminal 4: Frontend
Write-Host "🎨 Terminal 4: FRONTEND (Ejecutando en nueva ventana...)" -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectPath\Eva-Front'; npm start"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ TODOS LOS SERVICIOS HAN SIDO INICIADOS" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ ESPERA 40 SEGUNDOS a que todo se inicie..." -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 URLS para acceder:" -ForegroundColor White
Write-Host "   🌐 Frontend:    http://localhost:4200" -ForegroundColor Cyan
Write-Host "   🔌 Backend:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "   🧠 AI Service:  http://localhost:8001" -ForegroundColor Cyan
Write-Host "   📚 Ollama:      http://localhost:11434" -ForegroundColor Cyan
Write-Host ""
Write-Host "👤 Primero regístrate como EMPRESA:" -ForegroundColor White
Write-Host "   Email: empresa@test.com" -ForegroundColor Gray
Write-Host "   Password: test123" -ForegroundColor Gray
Write-Host ""
Read-Host "Presiona Enter para abrir el navegador"
Start-Process "http://localhost:4200"
