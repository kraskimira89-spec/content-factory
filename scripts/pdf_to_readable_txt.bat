@echo off
chcp 65001 > nul
cd /d D:\content-factory
call venv\Scripts\activate.bat 2>nul
echo.
echo Извлечение текста из PDF в .txt (UTF-8)
echo output/aroma\*.pdf -^> *.txt
echo.
set PYTHONIOENCODING=utf-8
python scripts\pdf_to_readable_txt.py %*
echo.
pause
