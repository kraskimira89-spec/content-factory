@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d D:\content-factory
call venv\Scripts\activate.bat
echo.
echo === Агент 1: генерация ключевых фраз ===
python seo-agents\agent1_keywords\agent_1_keywords.py
echo.
echo === Агент-планировщик: контент-план ===
python seo-agents\agent_planner\agent_planner.py
echo.
echo === Агент 2: создание ТЗ ===
python seo-agents\agent2_brief\agent_2_brief.py
echo.
echo === Агент 3: написание текста страницы ===
python seo-agents\agent3_content\agent_3_content.py
echo.
echo === Агент Editor: правка черновика, утверждение ===
python seo-agents\agent_editor\agent_editor.py
echo.
echo === Агент 8: планировщик картинок (prompts + alt) ===
python seo-agents\agent8_images_planner.py
echo.
echo === Агент 9: генератор картинок (ComfyUI/SD, пока заглушка) ===
python seo-agents\agent9_images_runner.py
echo.
echo === Агент 4: публикация в WordPress ===
python seo-agents\agent4_publish\agent_4_publish.py
echo.
echo === Publisher ВК: анонс в группу ===
python seo-agents\agent_publish_vk\agent_publish_vk.py
echo.
echo === Агент Analyst: пересчёт приоритетов ===
python seo-agents\agent_analyst\agent_analyst.py
echo.
echo === Готово! Файлы в папке output ===
pause
start "" "D:\content-factory\output"
