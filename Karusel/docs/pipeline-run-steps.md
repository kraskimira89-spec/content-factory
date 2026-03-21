# Прогон карусели Karusel по шагам

Пайплайн в коде: [`Karusel/agents/orchestrator.py`](../agents/orchestrator.py) (`run_pipeline` / async `run`). Все пути ниже — от корня репозитория `content-factory`, если не указано иное.

## Шаг 0. Подготовка (один раз)

1. Репозиторий: `D:\content-factory`, venv: `D:\content-factory\venv`.
2. Зависимости: из корня `pip install -r requirements.txt`.
3. Playwright: `playwright install chromium`.
4. Конфиг: в `config/.env` (корень content-factory) при необходимости ключи для **Parser** (LLM) и **Vision**, если включите его (см. ниже).
5. GPU для rembg (опционально): см. [`Karusel/docs/cuda12-rembg-gpu-windows.md`](cuda12-rembg-gpu-windows.md); для терминала Cursor удобно: [`Karusel/run-python-gpu.ps1`](../run-python-gpu.ps1) или [`Karusel/run-test-agents-2-3-gpu.ps1`](../run-test-agents-2-3-gpu.ps1). Проверка Vision/Rembg вручную: [`Karusel/tests/README.md`](../tests/README.md).

## Логика агентов (что происходит по порядку)

| № | Агент | Что делает |
|---|--------|------------|
| 1 | **Agent 1 (Parser)** | Текст ТЗ → структура `CarouselData` (слайды, бренд, тексты). |
| 2 | **Agent 2 (Vision)** | Анализ фото (лучший кадр персонажа и т.д.). **В CLI по умолчанию выключен** ([`Karusel/run_pipeline_cli.py`](../run_pipeline_cli.py) передаёт `run_vision=False`). В боте включается флагом `run_vision`. |
| 3 | **Agent 3 (Rembg)** | Вырезка персонажа (PNG) для слайдов с `use_character`. |
| 4 | **Agent 4 (Composer)** | Сборка данных для каждого слайда (Jinja-контекст). |
| 5 | **Agent 5 (Builder)** | Рендер HTML → JPG через Playwright (Chromium). |
| 6 | **Agent 6 (Poster)** | Отправка в Telegram. **В CLI по умолчанию выключен** (`run_poster=False`). |

## Шаг 1. Подготовить входные данные

- **Фото:** один или несколько `.jpg` / `.png` (пути без проблем с кириллицей по возможности).
- **ТЗ:** короткий текст или файл `.txt` с услугой, городом, телефоном, УТП и т.д.

Пример ТЗ в одну строку:

`Услуга: массаж спины. Город: Москва. Телефон: +7 900 000-00-00. Акцент: снятие напряжения за один сеанс.`

## Шаг 2. Запуск CLI (минимальный прогон)

Рабочая директория — **корень** `content-factory` (чтобы пути к фото и `--output` были предсказуемы).

Вставляйте в терминал **по одной строке**:

```powershell
cd D:\content-factory
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
python Karusel\run_pipeline_cli.py --photos-dir Karusel\demo_photos --brief-file Karusel\demo_brief.txt --output Karusel\out_demo
```

Свои фото (подставьте **реальные** пути, не шаблон «путь\к»):

```powershell
python Karusel\run_pipeline_cli.py --photos "C:\Users\Вы\Pictures\photo1.jpg" --brief "Услуга: массаж. Город: Москва. Телефон: +7..." --output Karusel\out_demo
```

## Шаг 3. Проверить результат

- В `--output` появятся **JPG слайдов** (и подпапка `chars` с вырезками, если rembg отработал).
- В консоли будет строка вида `Готово. Слайды: [...]`.

## Шаг 4. (Опционально) Другой визуальный бренд / карта Figma

См. примеры в `Karusel/README.md` (`--design-tokens`, `--figma-map`).

## Шаг 5. (Опционально) Сравнение пресетов / вариантов

Скрипты [`Karusel/render_compare_variants.cmd`](../render_compare_variants.cmd), [`Karusel/render_compare_variants_4.cmd`](../render_compare_variants_4.cmd) или [`Karusel/render_compare_variants.py`](../render_compare_variants.py) — см. [`Karusel/README.md`](../README.md) (нужны локальные `Karusel/demo_photos` и `Karusel/demo_brief.txt`, см. их README).

## Шаг 6. Запуск через бота (полный сценарий с Vision + отправкой)

```powershell
cd D:\content-factory
.\venv\Scripts\Activate.ps1
python Karusel\run_bot.py
```

Нужен `TELEGRAM_BOT_TOKEN` в `config/.env`. В хэндлере включается сценарий с фото + ТЗ в чате (см. [`Karusel/handlers/carousel_handler.py`](../handlers/carousel_handler.py)).

## Частые ошибки (по логам терминала)

| Симптом | Что сделать |
|--------|-------------|
| `FileNotFoundError: Фото не найдено` | В `--photos` / `--photos-dir` укажите существующие файлы. Для проверки используйте `Karusel\demo_photos` (см. пример выше). |
| `module 'playwright' has no attribute 'async_api'` | Часто устаревший локальный `agent5_builder.py`: в актуальной версии — `from playwright.async_api import async_playwright`. Выполните `git pull`, затем `pip install -U playwright` и `playwright install chromium`. |
| `TelegramNetworkError` / `Cannot connect to host api.telegram.org` | Проблема сети, VPN, файрвола или DNS. Проверьте браузером `https://api.telegram.org`, при необходимости другой DNS/VPN. |
| `Connection refused` к `127.0.0.1:8000` при `comfy_api/run_comfy_workflow.py` | ComfyUI не запущен или слушает другой порт. Запустите ComfyUI; при порте 8188: `COMFYUI_URL=http://127.0.0.1:8188` или `--server ...`. |

## Если rembg ругается на CUDA/cuDNN в терминале Cursor

**Вариант A** — один раз в этой сессии терминала:

```powershell
cd D:\content-factory
```

```powershell
$env:Path = "D:\content-factory\venv\Lib\site-packages\nvidia\cudnn\bin;" + $env:Path
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
python Karusel\run_pipeline_cli.py --photos-dir Karusel\demo_photos --brief-file Karusel\demo_brief.txt --output Karusel\out_demo
```

**Вариант B** — обёртка [`Karusel/run-python-gpu.ps1`](../run-python-gpu.ps1) (см. [`Karusel/docs/cuda12-rembg-gpu-windows.md`](cuda12-rembg-gpu-windows.md)): укажите `-ScriptPath` на `Karusel\run_pipeline_cli.py`, `-WorkingDirectory` на `D:\content-factory`, остальное передайте как аргументы Python **без** `--` в PowerShell.
