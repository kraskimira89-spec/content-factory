@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\content-factory
call venv\Scripts\activate.bat 2>nul
echo.
echo === Agent9: генерация картинок для ароматерапии ===
echo Сначала убедись: SD WebUI запущен с --api, http://127.0.0.1:7860/docs открывается.
echo.
python seo-agents\agent9_images_runner.py --plan-json output\20260304_135503_page_Ароматерапия_Ноябрьск.images-plan.json --output-json output\20260304_135503_page_Ароматерапия_Ноябрьск.images-generated.json --slug aromaterapiya
echo.
echo После успешного прогона обнови страницу в WP:
echo   python seo-agents\agent4_publish\agent_4_publish.py aromaterapiya
echo.
pause
