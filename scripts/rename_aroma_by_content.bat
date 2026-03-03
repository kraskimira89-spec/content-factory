@echo off
chcp 65001 > nul
cd /d D:\content-factory
call venv\Scripts\activate.bat 2>nul
echo.
echo Переименование файлов в output/aroma по содержимому
echo.
set PYTHONIOENCODING=utf-8
python scripts\rename_aroma_by_content.py
echo.
pause
