@echo off
chcp 65001 > nul
cd /d D:\content-factory
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo venv не найден. Запуск через python...
)
echo.
echo === Парсер Gloryon: эфирные масла ===
echo Браузер: Yandex + YandexDriver (scripts/drivers/yandexdriver.exe)
echo Скачать: https://github.com/yandex/YandexDriver/releases
echo Старт: https://www.gloryon.com/site/catalog/10900
echo Вкладки: Презентация, Описание, Состав, Применение, Мой SMM, Истории
echo Результат: D:\content-factory\output\aroma\*.md
echo.
echo Опции: --together (режим вместе) --browser chrome --limit N
echo.
set PYTHONIOENCODING=utf-8
python scripts\parse_gloryon_aroma.py --browser yandex %*
echo.
start "" "D:\content-factory\output\aroma"
pause
