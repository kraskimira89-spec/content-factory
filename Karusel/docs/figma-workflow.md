# Figma Workflow Для Karusel

## Цель

Figma в `Karusel` используется как источник:

- макетов слайдов `1080x1350`
- дизайн-токенов
- бренд-ассетов
- референса для HTML/Jinja шаблонов

Итоговый пайплайн:

`Figma -> JSON токены + ассеты -> HTML/CSS шаблоны -> Playwright -> JPG -> Telegram`

## Что делать в Figma

Один master-файл должен содержать 8 фреймов:

1. `cover`
2. `benefits`
3. `indications`
4. `howworks`
5. `target_audience`
6. `results`
7. `photo_raw`
8. `cta`

Для каждого фрейма задавать:

- размер `1080x1350`
- safe area для текста
- положение персонажа `left/right`
- карточки, буллеты, CTA и телефон как повторно используемые компоненты

## Куда складывать экспорт из Figma

### Токены

Основной файл:

- `Karusel/config/brand_colors.json`
- `Karusel/config/figma_template_map.json`
- `Karusel/config/demo_figma_template_map_alt.json`
- `Karusel/config/demo_brand_tokens_ocean_med.json`
- `Karusel/config/demo_brand_tokens_premium_gold.json`

Зеркало рядом с бренд-ассетами:

- `Karusel/assets/carousel/brand/colors.json`

Builder автоматически читает эти файлы и превращает токены в CSS variables.
Отдельно `figma_template_map.json` связывает названия фреймов в Figma с HTML-шаблонами и layout-настройками.
Для тестов другого бренда можно передать отдельный JSON токенов через CLI.
При необходимости можно также передать альтернативную карту Figma frame -> template через CLI.

### Ассеты

Ожидаемые пути (создайте при экспорте из Figma; в репозитории могут отсутствовать до первого экспорта):

- логотип: `Karusel/assets/carousel/brand/logo.png`
- иконки: `Karusel/assets/carousel/icons/*.png`
- дополнительные декоры: `Karusel/assets/carousel/decorations/*`

Подробнее: [`Karusel/assets/carousel/README.md`](../assets/carousel/README.md).

## Какие токены сейчас поддерживаются

```json
{
  "frame_size": { "width": 1080, "height": 1350 },
  "colors": {
    "primary": "#FFE033",
    "yellow_light": "#FFF3A0",
    "yellow_dark": "#E6C800",
    "black": "#000000",
    "white": "#FFFFFF",
    "gray": "#444444",
    "gray_light": "#F5F5F5"
  },
  "radii": {
    "card": "16px",
    "small": "10px"
  },
  "typography": {
    "font_family": "'Inter', sans-serif",
    "title_size": "68px",
    "subtitle_size": "32px",
    "body_size": "30px"
  },
  "shadows": {
    "card": "0 4px 20px rgba(0,0,0,0.10)",
    "heavy": "0 8px 32px rgba(0,0,0,0.18)"
  },
  "assets": {
    "logo": "assets/carousel/brand/logo.png"
  }
}
```

### Точечные overrides по имени Figma frame

Поддерживается секция:

```json
{
  "frame_overrides": {
    "Cover": {
      "overlay_opacity": "0.62",
      "character_height": "980px"
    },
    "CTA": {
      "content_top": "120px",
      "cta_phone_size": "48px"
    }
  }
}
```

Порядок приоритета такой:

1. общие `layout`
2. `template_layouts` по `slide type`
3. `frame_overrides` по `frame_name` из `figma_template_map.json`

То есть настройки конкретного Figma frame имеют наивысший приоритет.

## Как это связано с кодом

- `Karusel/agents/agent5_builder.py`
  - читает токены из JSON
  - читает `figma_template_map.json`
  - превращает их в CSS variables
  - подставляет `logo_path`, если есть экспортированный логотип
  - берет размеры фрейма для viewport рендера
  - прокидывает в шаблоны `figma_frame_name` и `layout`

- `Karusel/templates/carousel/base.css`
  - использует CSS variables для цветов, размеров, типографики и размеров слайда

- `Karusel/templates/carousel/*.html`
  - повторяют композицию фреймов Figma, но наполняются данными автоматически

## Правило переноса макета из Figma в шаблон

1. Сначала перенести общие токены в `brand_colors.json`
2. Затем зафиксировать названия фреймов в `figma_template_map.json`
3. Затем экспортировать логотип/иконки в `Karusel/assets/carousel/...`
4. Только после этого переносить layout в `*.html`
5. Переиспользовать существующие классы из `base.css`, а не добавлять уникальный inline-стиль на каждый элемент

## Как проверить другой бренд без правки HTML

Для примеров ниже нужны локальные входные данные: положите фото в [`Karusel/demo_photos`](../demo_photos/README.md) и при необходимости отредактируйте [`Karusel/demo_brief.txt`](../demo_brief.txt).

В проекте есть demo-файлы конфигов:

- `Karusel/config/demo_brand_tokens_ocean_med.json`
- `Karusel/config/demo_brand_tokens_premium_gold.json`
- `Karusel/config/demo_figma_template_map_alt.json`

Пример запуска:

```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos-dir .\Karusel\demo_photos --brief-file .\Karusel\demo_brief.txt --design-tokens .\Karusel\config\demo_brand_tokens_ocean_med.json --output .\Karusel\out_ocean_demo
```

Пример запуска с премиальным брендом и явной картой Figma:

```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos-dir .\Karusel\demo_photos --brief-file .\Karusel\demo_brief.txt --design-tokens .\Karusel\config\demo_brand_tokens_premium_gold.json --figma-map .\Karusel\config\figma_template_map.json --output .\Karusel\out_premium_demo
```

Пример запуска с альтернативной композицией:

```bash
cd D:\content-factory
python Karusel/run_pipeline_cli.py --photos-dir .\Karusel\demo_photos --brief-file .\Karusel\demo_brief.txt --design-tokens .\Karusel\config\demo_brand_tokens_premium_gold.json --figma-map .\Karusel\config\demo_figma_template_map_alt.json --output .\Karusel\out_premium_alt_demo
```

Быстрое пакетное сравнение трех брендов:

```bat
cd D:\content-factory\Karusel
render_compare_variants.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
```

Быстрое пакетное сравнение четырех наборов, включая `premium_alt`:

```bat
cd D:\content-factory\Karusel
render_compare_variants_4.cmd "D:\content-factory\Karusel\demo_photos" "D:\content-factory\Karusel\demo_brief.txt"
```

Python-обёртка с красивым summary и пятью наборами:

```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --output-root Karusel/compare_out_py
```

Только выбранные варианты:

```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt --output-root Karusel/compare_out_py
```

С автооткрытием HTML-отчёта:

```bash
cd D:\content-factory
python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt --output-root Karusel/compare_out_py --open-report
```

В этом режиме рендерятся:

- `default`
- `ocean`
- `ocean_alt`
- `premium`
- `premium_alt`

После выполнения в `output-root` автоматически создается `index.html` со ссылками на все папки результатов, краткой таблицей summary и мини-лентой из первых 2–3 слайдов каждого варианта.

Если в макете меняются только токены и layout, HTML-шаблоны трогать не нужно.

## Соответствие Figma -> шаблон

Пути от корня репозитория `content-factory`:

- Frame `cover` -> `Karusel/templates/carousel/cover.html`
- Frame `benefits` -> `Karusel/templates/carousel/benefits.html`
- Frame `indications` -> `Karusel/templates/carousel/indications.html`
- Frame `howworks` -> `Karusel/templates/carousel/howworks.html`
- Frame `target_audience` -> `Karusel/templates/carousel/target_audience.html`
- Frame `results` -> `Karusel/templates/carousel/results.html`
- Frame `photo_raw` -> `Karusel/templates/carousel/photo_raw.html`
- Frame `cta` -> `Karusel/templates/carousel/cta.html`

## Практический совет

Если в Figma меняется только цвет/типографика/радиусы, достаточно обновить JSON токенов.

Если меняется композиция блока, тогда нужно править соответствующий `*.html` шаблон.
