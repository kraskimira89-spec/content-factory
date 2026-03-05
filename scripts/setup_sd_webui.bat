@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: SD_WEBUI_ROOT: из переменной окружения или config\.env
if "%SD_WEBUI_ROOT%"=="" (
  set "_env=%~dp0..\config\.env"
  if exist "!_env!" (
    for /f "usebackq tokens=1,* delims==" %%a in ("!_env!") do (
      if "%%~a"=="SD_WEBUI_ROOT" set "SD_WEBUI_ROOT=%%~b"
    )
  )
)
if "%SD_WEBUI_ROOT%"=="" set "SD_WEBUI_ROOT=D:\AI\stable-diffusion-webui"

title Настройка SD WebUI — %SD_WEBUI_ROOT%
color 0A

echo.
echo ============================================
echo   Полная настройка SD WebUI для content-factory
echo   SD_WEBUI_ROOT = %SD_WEBUI_ROOT%
echo   Открой в браузере: http://127.0.0.1:7860
echo ============================================
echo.
echo [0] Запусти WebUI: cd "%SD_WEBUI_ROOT%"
echo     webui-user.bat  ^(или webui.bat --api^)
echo     В webui-user.bat должно быть: set COMMANDLINE_ARGS=--api
echo     Если 7860 занят, откроется 7861, 7862 и т.д.
echo     Смотри в консоли "Running on local URL: http://127.0.0.1:ПОРТ"
echo     Укажи этот URL в config/.env: SD_WEBUI_URL=http://127.0.0.1:ПОРТ
echo.
echo     Если лог засоряет facechain: переименуй extensions\facechain в _facechain_disabled.
echo     Подробно: docs\sd-webui-api-agent9.md
echo.
pause

:: ========== TXT2IMG ==========
echo.
echo ========== ВКЛАДКА TXT2IMG ==========
echo.

echo [1] Checkpoint ^(модель^): выбери нужную SD-модель.
echo     Рекомендуется SD 1.5 или SDXL для качественных иллюстраций.
echo.
pause

echo [2] VAE: оставь "None" или выбери VAE для модели.
echo     Некоторые модели имеют встроенный VAE.
echo.
pause

echo [3] Sampler: DPM++ 2M Karras ^(или DPM++ 2M^).
echo     shared-config: sampler_name = DPM++ 2M
echo.
pause

echo [4] Sampling steps: 24 ^(или 25^).
echo     shared-config: steps = 24
echo.
pause

echo [5] Width / Height: 1280 x 720 ^(hero по умолчанию^).
echo     agent9 передаёт размеры в запросе, можно оставить любые.
echo.
pause

echo [6] Batch count: 1. Batch size: 1.
echo.
pause

echo [7] CFG Scale: 7.
echo     shared-config: cfg_scale = 7
echo.
pause

echo [8] Seed: -1 ^(случайный^) или фиксированное для воспроизводимости.
echo.
pause

echo [9] Negative prompt ^(рекомендуемый^):
echo     blurry, low quality, distorted, text, watermark, logo
echo.
pause

echo [10] Restore faces: выключено ^(по умолчанию^).
echo      Включи, если генерируешь лица.
echo.
pause

echo [11] Tiling: выключено.
echo.
pause

echo [12] Hires. fix: выключено по умолчанию.
echo      Включи для увеличения разрешения ^(медленнее^).
echo.
pause

echo [13] Scripts: оставь пустым для agent9.
echo.
pause

:: ========== IMG2IMG ==========
echo.
echo ========== ВКЛАДКА IMG2IMG ==========
echo.

echo [14] Перейди во вкладку "img2img".
echo      Denoising strength: 0.75 ^(по умолчанию^).
echo      Resize mode: Just resize / Crop and resize — по задаче.
echo.
pause

echo [15] Inpaint: при необходимости маски.
echo      Inpaint at full resolution — по вкусу.
echo.
pause

:: ========== EXTRAS ==========
echo.
echo ========== ВКЛАДКА EXTRAS ==========
echo.

echo [16] Перейди во вкладку "Extras".
echo      Single image / Batch process — для апскейла.
echo      Upscaler: RealESRGAN 4x+ или ESRGAN_4x.
echo.
pause

:: ========== PNG INFO ==========
echo.
echo [17] Перейди во вкладку "PNG Info".
echo      Сюда можно загрузить картинку и посмотреть промпт/параметры.
echo.
pause

:: ========== SETTINGS ==========
echo.
echo ========== ВКЛАДКА SETTINGS ==========
echo.

echo [18] Перейди в Settings — General.
echo      Cross attention optimization: xformers или Automatic.
echo      Automatically open WebUI in browser: по желанию.
echo.
pause

echo [19] Settings — User interface.
echo      Localization: по желанию.
echo      Quick settings list: добавь часто используемые параметры.
echo.
pause

echo [20] Settings — Generation.
echo      Filter NSFW: по желанию.
echo      Если картинки получаются серыми квадратами — отключи "Filter NSFW" / Safety checker.
echo      Add model name to generation info: Да.
echo.
pause

echo [21] Settings — Saving images.
echo      Save images in subfolder: Year-Month ^(рекомендуется^).
echo      Save a copy of image to a directory: опционально.
echo      Write infotext to txt file: Да.
echo      Images format: png ^(без потерь^) или jpg ^(меньше размер^).
echo      Image quality for JPEG: 95.
echo.
pause

echo [22] Settings — Upscaling.
echo      RealESRGAN / ESRGAN model path — проверь пути.
echo.
pause

echo [23] Settings — Stable Diffusion.
echo      SD Model checkpoint: выбери основную модель.
echo      SD VAE: Auto / None или конкретный VAE.
echo      CLIP skip: 1 ^(SD 1.5^) или 2 ^(некоторые модели^).
echo.
pause

echo [24] Settings — Optimizations.
echo      Sd attention: xformers / Automatic.
echo      Use upcast attention: при нехватке VRAM.
echo.
pause

echo [25] Settings — Interrogate.
echo      CLIP / DeepBooru для анализа картинок — по необходимости.
echo.
pause

echo [26] Сохрани настройки: кнопка "Apply settings" внизу.
echo      Затем "Reload UI" при необходимости.
echo.
pause

:: ========== CHECKPOINTS / LORA ==========
echo.
echo [27] Проверь модели: Stable Diffusion checkpoint загружен.
echo      LoRA ^(если используются^): добавь в prompts.
echo.
pause

:: ========== API ==========
echo.
echo [28] API доступен при --api: http://127.0.0.1:7860/docs
echo      agent9 использует POST /sdapi/v1/txt2img
echo.
pause

echo.
echo ============================================
echo   Настройка завершена. Можно запускать agent9.
echo ============================================
echo.
pause
