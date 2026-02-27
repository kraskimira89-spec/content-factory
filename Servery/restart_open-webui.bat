@echo off
chcp 65001 > nul
echo Перезапуск Open WebUI...

echo Остановка сервера (порт 8080)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /PID %%a /F 2>nul
)

echo Ожидание...
timeout /t 3 /nobreak > nul

echo Запуск сервера...
start "" open-webui serve
echo Ожидание запуска...
timeout /t 5 /nobreak > nul
start http://localhost:8080/
echo Готово.
