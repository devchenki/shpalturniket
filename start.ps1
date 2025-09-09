# Shaplych Monitoring System Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Shaplych Monitoring System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.8+" -ForegroundColor Red
    exit 1
}

# Проверяем наличие Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js найден: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не найден! Установите Node.js 16+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Запуск backend сервера..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8771 --reload"

Write-Host "⏳ Ожидание запуска backend..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "🚀 Запуск frontend сервера..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --port 5180"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Система запущена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8771" -ForegroundColor Blue
Write-Host "Frontend: http://localhost:5180" -ForegroundColor Blue
Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
