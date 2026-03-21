# Karusel — агент карусели для TG/соцсетей

Пайплайн: фото + ТЗ → 6 агентов → слайды 1080×1350 (JPG) → альбом в Telegram.

## Структура

- **agents/** — Agent 1 (Parser), 2 (Vision), 3 (Rembg), **3b (CharGen, опционально ComfyUI)**, 4 (Composer), 5 (Builder), 6 (Poster), orchestrator
- **templates/carousel/** — HTML-шаблоны слайдов (Jinja2) + base.css
- **models/** — Pydantic: CarouselData, SlideData, Brand
- **handlers/** — TG-хэндлер (car:enter → ожидание фото + ТЗ)
- **assets/carousel/** — `brand/colors.json`; опционально `brand/logo.png`, `icons/`, `decorations/` (см. `Karusel/assets/carousel/README.md`)
- **prompts/** — только Agent 1: `agent1_parser.txt` (см. `Karusel/prompts/README.md`)
- **demo_photos/** — положите сюда jpg/png для примеров с `--photos-dir` (см. `Karusel/demo_photos/README.md`); **demo_brief.txt** — пример ТЗ в корне `Karusel/`

## Зависимости

Уже добавлены в корневой `requirements.txt`: rembg, playwright, jinja2, aiogram>=3, pydantic.

После установки выполнить: `playwright install chromium`.

### rembg и CUDA (ошибка `cublasLt64_12.dll` / onnxruntime_providers_cuda)

Если в логах **onnxruntime** пишет про отсутствие **CUDA** или **cublasLt64_12.dll** — у вас стоит GPU-сборка без полного CUDA Toolkit 12. Варианты:

1. **Проще — только CPU** (рекомендуется без видеокарты NVIDIA / без CUDA):
   ```powershell
   pip uninstall onnxruntime onnxruntime-gpu -y
   pip install onnxruntime
   pip install -r requirements.txt
   ```
   В `requirements.txt` указан обычный `rembg` (без `[gpu]`).

2. **GPU (ускорение rembg)** — пошагово на Windows: **`Karusel/docs/cuda12-rembg-gpu-windows.md`** (драйвер → CUDA Toolkit 12 → `onnxruntime-gpu` → проверка). Кратко: после Toolkit выполните `pip uninstall onnxruntime onnxruntime-gpu -y` и `pip install onnxruntime-gpu`, затем проверьте `CUDAExecutionProvider`. **Ollama** GPU обычно работает от драйвера отдельно от этого пайплайна.

### Целевая среда Karusel (Production/Dev)

- **Целевая среда:** GPU (NVIDIA RTX 3060+), Windows 10/11, Python 3.11.
- **Vision backend по умолчанию:** локальный Ollama (`VISION_BACKEND=ollama`, `OLLAMA_VISION_MODEL=llava`).
- **Rembg backend:** `onnxruntime-gpu` + `CUDAExecutionProvider`.
- **Критерий готовности окружения:**
  ```powershell
  python -c "import onnxruntime as ort; print(ort.get_available_providers())"
  ```
  В ответе должен быть `CUDAExecutionProvider`.
- **Фактический статус (зафиксировано):** `['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`.

## Конфиг

- `config/.env` (корень content-factory): `TELEGRAM_BOT_TOKEN`.
- **Vision (анализ фото):**
  - **OpenAI / прокси:** `OPENAI_API_KEY`, опционально `OPENAI_BASE_URL`, `OPENAI_MODEL` (например `gpt-4o`).
  - **Локальный Ollama:** `VISION_BACKEND=ollama`, `OLLAMA_URL=http://localhost:11434`, `OLLAMA_VISION_MODEL=llava` или `llava:13b` (модель с vision: `ollama pull llava`).
- Цвета и дизайн-токены: `Karusel/config/brand_colors.json` и `Karusel/assets/carousel/brand/colors.json`.
- Явная связь Figma frame -> HTML template: `Karusel/config/figma_template_map.json`.
- **Presets** (размер, safe area, character_box): `Karusel/config/presets/` — `telegram_portrait.json`, `instagram_square.json`, `story_9x16.json`. Используются при передаче `preset_path` в пайплайн/билдер.
- **Export profiles** (платформа → preset): `Karusel/config/export_profiles.json` — `telegram_album`, `instagram_feed_portrait`, `instagram_feed_square`, `stories_9x16`, `vk_feed`. В качестве `preset_path` можно передать id профиля (например `telegram_album`).
- Альтернативная demo-карта композиции: `Karusel/config/demo_figma_template_map_alt.json`.
- Demo-бренд для проверки без правки HTML: `Karusel/config/demo_brand_tokens_ocean_med.json`.
- Premium demo-бренд для сравнения визуального направления: `Karusel/config/demo_brand_tokens_premium_gold.json`.
- Figma workflow: `Karusel/docs/figma-workflow.md`.

### Генерация персонажа через ComfyUI (Agent 3b, опционально)

По умолчанию выключено. При **`CHAR_VARIATION_ENABLED=1`** оркестратор параллельно с rembg вызывает ComfyUI, генерирует PNG на слайд (поза/фон из [`Karusel/config/character_variation_presets.json`](config/character_variation_presets.json)), затем прогоняет результат через rembg. В **Agent 4** приоритет: **AI (`char_per_slide`) > rembg > без персонажа**.

Переменные окружения (в `config/.env` или перед запуском):

| Переменная | Описание |
|------------|----------|
| `CHAR_VARIATION_ENABLED` | `1` / `true` — включить Agent 3b |
| `COMFYUI_URL` | Базовый URL, по умолчанию `http://127.0.0.1:8000` (ComfyUI 0.15+; старые сборки — `:8188`, задайте явно) |
| `COMFYUI_CHECKPOINT` | Имя чекпоинта (перекрывает JSON), напр. `realisticVision_v60B1VAE.safetensors` |
| `CHAR_ON_EVERY_SLIDE` | `1` / `true` — генерировать персонажа для всех слайдов кроме `photo_raw` и `cta` (даже если Parser выставил `use_character=false`) |

Workflow API: [`Karusel/assets/carousel/comfyui_portrait.json`](assets/carousel/comfyui_portrait.json) — ноды `3`–`9` как в стандартном txt2img; checkpoint в JSON должен существовать в папке моделей ComfyUI.

Если ComfyUI недоступен или генерация падает, пайплайн продолжает работу с **rembg** как раньше.

## Запуск

**CLI (без бота):**
```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos img1.jpg img2.jpg --brief "Услуга: Массаж. Город: Москва. Телефон: +7..." --output Karusel/out
```

**CLI с альтернативными Figma-токенами бренда:**
```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos img1.jpg img2.jpg --brief "Услуга: Массаж. Город: Москва. Телефон: +7..." --design-tokens Karusel/config/demo_brand_tokens_ocean_med.json --output Karusel/out_ocean
```

**CLI с альтернативными токенами и картой Figma:**
```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos img1.jpg img2.jpg --brief "Услуга: Массаж. Город: Москва. Телефон: +7..." --design-tokens Karusel/config/demo_brand_tokens_premium_gold.json --figma-map Karusel/config/figma_template_map.json --output Karusel/out_premium
```

**CLI с альтернативной композицией (`alt` map):**
```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos img1.jpg img2.jpg --brief "Услуга: Массаж. Город: Москва. Телефон: +7..." --design-tokens Karusel/config/demo_brand_tokens_premium_gold.json --figma-map Karusel/config/demo_figma_template_map_alt.json --output Karusel/out_premium_alt
```

**Batch-сравнение `default / ocean / premium`:**
```bat
cd D:\content-factory\Karusel
render_compare_variants.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
```

**Batch-сравнение `default / ocean / premium / premium_alt`:**
```bat
cd D:\content-factory\Karusel
render_compare_variants_4.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
```

**Python-обёртка с summary для `default / ocean / ocean_alt / premium / premium_alt`:**
```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --output-root Karusel/compare_out_py
```

**Python-обёртка только для выбранных вариантов:**
```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt --output-root Karusel/compare_out_py
```

**Python-обёртка с автооткрытием HTML-отчёта:**
```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt --output-root Karusel/compare_out_py --open-report
```

После рендера рядом создается `index.html` со ссылками на папки результатов, кратким summary и мини-лентой из первых 2–3 слайдов каждого варианта.

Команды с `demo_photos` / `demo_brief.txt` требуют локальных фото в `Karusel/demo_photos/` (файлы по умолчанию не в git — см. `demo_photos/README.md`) и при необходимости правки `Karusel/demo_brief.txt`.

**TG-бот:**
```bash
cd D:\content-factory
python Karusel/run_bot.py
```
В боте: callback `car:enter` (кнопка «Карусель») → пришлите фото (до 10) → отправьте текст ТЗ отдельным сообщением.

## Иконки для слайда «Кому полезно»

Положите в `Karusel/assets/carousel/icons/` файлы с именами, содержащими подсказки: office, sport, vakht, elderly и т.д. (например office.png, sport.png). Agent 4 подставит их по полю `icon_hints` в слайд типа `target`.
