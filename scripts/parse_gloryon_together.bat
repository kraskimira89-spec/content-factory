@echo off
chcp 65001 > nul
cd /d D:\content-factory
call venv\Scripts\activate.bat 2>nul
echo.
echo === Gloryon: режим ВМЕСТЕ ===
echo.
echo Ты открываешь страницы и вкладки в браузере.
echo Скрипт читает по нажатию Enter и сохраняет в output/aroma\
echo.
echo 1. Появится браузер с каталогом
echo 2. Залогинься, открой нужное масло
echo 3. Открой вкладку (Презентация, Описание, Состав...)
echo 4. Нажми Enter в этом окне - скрипт прочитает
echo 5. "Дальше" - следующая вкладка
echo.
echo Опции: --limit N (только первые N масел)
echo.
set PYTHONIOENCODING=utf-8
python scripts\parse_gloryon_aroma.py --together --browser yandex %*
echo.
start "" "D:\content-factory\output\aroma"
pause
