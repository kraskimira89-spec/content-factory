# Karusel — агент карусели для TG/соцсетей

Пайплайн: фото + ТЗ → 6 агентов → слайды 1080×1350 (JPG) → альбом в Telegram.

## Структура

- **agents/** — Agent 1 (Parser), 2 (Vision), 3 (Rembg), 4 (Composer), 5 (Builder), 6 (Poster), orchestrator
- **templates/carousel/** — HTML-шаблоны слайдов (Jinja2) + base.css
- **models/** — Pydantic: CarouselData, SlideData, Brand
- **handlers/** — TG-хэндлер (car:enter → ожидание фото + ТЗ)
- **assets/carousel/** — brand/colors.json, icons/ (office.png, sport.png, vakht.png, elderly.png и т.д.), decorations/
- **prompts/** — agent1_parser.txt (системный промпт для Parser)

## Зависимости

Уже добавлены в корневой `requirements.txt`: rembg, playwright, jinja2, aiogram>=3, pydantic.

После установки выполнить: `playwright install chromium`.

## Конфиг

- `config/.env` (корень content-factory): `TELEGRAM_BOT_TOKEN`, при использовании Vision — `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` (например gpt-4o для vision).
- Цвета и дизайн-токены: `Karusel/config/brand_colors.json` и `Karusel/assets/carousel/brand/colors.json`.
- Явная связь Figma frame -> HTML template: `Karusel/config/figma_template_map.json`.
- **Presets** (размер, safe area, character_box): `Karusel/config/presets/` — `telegram_portrait.json`, `instagram_square.json`, `story_9x16.json`. Используются при передаче `preset_path` в пайплайн/билдер.
- **Export profiles** (платформа → preset): `Karusel/config/export_profiles.json` — `telegram_album`, `instagram_feed_portrait`, `instagram_feed_square`, `stories_9x16`, `vk_feed`. В качестве `preset_path` можно передать id профиля (например `telegram_album`).
- Альтернативная demo-карта композиции: `Karusel/config/demo_figma_template_map_alt.json`.
- Demo-бренд для проверки без правки HTML: `Karusel/config/demo_brand_tokens_ocean_med.json`.
- Premium demo-бренд для сравнения визуального направления: `Karusel/config/demo_brand_tokens_premium_gold.json`.
- Figma workflow: `Karusel/docs/figma-workflow.md`.

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

**TG-бот:**
```bash
cd D:\content-factory
python Karusel/run_bot.py
```
В боте: callback `car:enter` (кнопка «Карусель») → пришлите фото (до 10) → отправьте текст ТЗ отдельным сообщением.

## Иконки для слайда «Кому полезно»

Положите в `Karusel/assets/carousel/icons/` файлы с именами, содержащими подсказки: office, sport, vakht, elderly и т.д. (например office.png, sport.png). Agent 4 подставит их по полю `icon_hints` в слайд типа `target`.
