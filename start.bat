@echo off
echo ========================================
echo   Shaplych Monitoring System
echo ========================================
echo.

echo Запуск backend сервера...
start "Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8771 --reload"

echo Ожидание запуска backend...
timeout /t 3 /nobreak > nul

echo Запуск frontend сервера...
start "Frontend" cmd /k "cd frontend && npm run dev -- --port 5180"

echo.
echo ========================================
echo   Система запущена!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8771
echo Frontend: http://localhost:5180
echo.
echo Нажмите любую клавишу для выхода...
pause > nul
