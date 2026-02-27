@echo off
chcp 65001 > nul
echo Запуск Open WebUI...
start "" open-webui serve
echo Ожидание запуска сервера...
timeout /t 5 /nobreak > nul
start http://localhost:8080/
echo Браузер открыт. Сервер работает в отдельном окне.
