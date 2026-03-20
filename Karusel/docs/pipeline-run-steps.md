# Прогон карусели Karusel по шагам

Пайплайн в коде: `agents/orchestrator.py` (`run_pipeline` / async `run`).

## Шаг 0. Подготовка (один раз)

1. Репозиторий: `D:\content-factory`, venv: `D:\content-factory\venv`.
2. Зависимости: из корня `pip install -r requirements.txt`.
3. Playwright: `playwright install chromium`.
4. Конфиг: в `config/.env` (корень content-factory) при необходимости ключи для **Parser** (LLM) и **Vision**, если включите его (см. ниже).
5. GPU для rembg (опционально): см. `docs/cuda12-rembg-gpu-windows.md`; для терминала Cursor удобно: `run-python-gpu.ps1` или `run-test-agents-2-3-gpu.ps1`.

## Логика агентов (что происходит по порядку)

| № | Агент | Что делает |
|---|--------|------------|
| 1 | **Agent 1 (Parser)** | Текст ТЗ → структура `CarouselData` (слайды, бренд, тексты). |
| 2 | **Agent 2 (Vision)** | Анализ фото (лучший кадр персонажа и т.д.). **В CLI по умолчанию выключен** (`run_pipeline_cli.py` передаёт `run_vision=False`). В боте включается флагом `run_vision`. |
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
python Karusel\run_pipeline_cli.py --photos "D:\путь\к\фото1.jpg" "D:\путь\к\фото2.jpg" --brief "Услуга: массаж. Город: Москва. Телефон: +7..." --output Karusel\out_demo
```

Или папка с фото + файл ТЗ:

```powershell
python Karusel\run_pipeline_cli.py --photos-dir "D:\путь\к\папке_с_фото" --brief-file "D:\путь\к\tz.txt" --output Karusel\out_demo
```

## Шаг 3. Проверить результат

- В `--output` появятся **JPG слайдов** (и подпапка `chars` с вырезками, если rembg отработал).
- В консоли будет строка вида `Готово. Слайды: [...]`.

## Шаг 4. (Опционально) Другой визуальный бренд / карта Figma

См. примеры в `Karusel/README.md` (`--design-tokens`, `--figma-map`).

## Шаг 5. (Опционально) Сравнение пресетов / вариантов

Скрипты `render_compare_variants.cmd`, `render_compare_variants_4.cmd` или `render_compare_variants.py` — см. `README.md`.

## Шаг 6. Запуск через бота (полный сценарий с Vision + отправкой)

```powershell
cd D:\content-factory
.\venv\Scripts\Activate.ps1
python Karusel\run_bot.py
```

Нужен `TELEGRAM_BOT_TOKEN` в `config/.env`. В хэндлере включается сценарий с фото + ТЗ в чате (см. `handlers/carousel_handler.py`).

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
python Karusel\run_pipeline_cli.py --photos-dir "D:\путь\к\фото" --brief-file "D:\путь\к\tz.txt" --output Karusel\out_demo
```

**Вариант B** — обёртка `run-python-gpu.ps1` (см. `docs/cuda12-rembg-gpu-windows.md`): укажите `-ScriptPath` на `run_pipeline_cli.py`, `-WorkingDirectory` на `D:\content-factory`, остальное передайте как аргументы Python **без** `--` в PowerShell.
