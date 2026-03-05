@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo.
echo === Генерация изображений для agent9 ===
echo.
echo Agent9 использует (по порядку):
echo   1. ComfyUI на COMFYUI_URL (по умолчанию :8188) или Flask API
echo   2. SD WebUI на SD_WEBUI_URL (по умолчанию :7860) - sdapi/v1/txt2img
echo.
echo Запустите Stable Diffusion WebUI с API:
echo   cd C:\путь\к\stable-diffusion-webui
echo   webui.bat --api
echo.
echo Или настройте config/.env:
echo   SD_WEBUI_URL=http://127.0.0.1:7860
echo.
pause
