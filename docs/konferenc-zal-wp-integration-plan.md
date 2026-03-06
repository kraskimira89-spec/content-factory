# План интеграции: JSON‑лендинги конференц‑зала → WordPress

**Цель:** публиковать 3 страницы конференц‑зала (под разные ЦА) из JSON в WordPress без ручной вставки.

---

## 1. Текущее состояние

| Компонент | Статус |
|-----------|--------|
| MD‑шаблон, JSON‑версии под ЦА | ✅ Готово |
| Промпт для LLM | ✅ `prompts/konferenc-zal-rewrite.md` |
| Протокол для агента | ✅ `docs/konferenc-zal-json-protocol.md` |
| Публикация в WP | ⚠️ Ручная вставка |
| agent4_publish | Публикует страницы услуг из **Markdown** (uslugi/*) |
| deploy_to_vps | Публикует **service_data** (results, faq, steps) в wp_options |

**Разрыв:** agent4 работает с Markdown → HTML. JSON‑лендинги — иной формат (hero, for_whom, benefits и т.д.), их нужно либо конвертировать, либо отдавать в отдельный эндпоинт.

---

## 2. Три страницы под ЦА

| ЦА | audience | slug (вариант) | JSON |
|----|---------|----------------|------|
| Корпоративные тренинги | corporate_trainings | `konferenc-zal/korporativnye-treningi` | konferenc-zal-corporate-training.json |
| Онлайн‑школы, вебинары | online_schools | `konferenc-zal/onlajn-shkoly` | konferenc-zal-online-school.json |
| Коучи, консультанты | coaches_consultants | `konferenc-zal/kouchting` | konferenc-zal-coaches.json |

Родитель: `konferenc-zal` (или отдельная страница «Конференц‑зал» как хаб).

---

## 3. Два подхода к публикации

### 3.1. Вариант A: новый REST‑эндпоинт на VPS

**Идея:** `POST /wp-json/entuziastov75/v1/landing-data/{slug}` принимает JSON‑блоки, сохраняет в wp_options. PHP‑шаблон выводит данные.

**Плюсы:** полный контроль над структурой, можно менять разметку без регенерации.  
**Минусы:** нужны правки в entuziastov75-vps (регистрация эндпоинта, шаблон).

**Контракт в shared-config.json:**
```json
"landing_data": {
  "path": "/wp-json/entuziastov75/v1/landing-data/{slug}",
  "methods": ["GET", "POST"]
}
```

### 3.2. Вариант B: JSON → HTML, обновление post_content

**Идея:** скрипт конвертирует JSON в семантический HTML (секции с классами), обновляет `post_content` через `PUT /wp-json/wp/v2/pages/{id}`. Работает с текущим WP без правок на VPS.

**Плюсы:** не требует изменений на VPS, использует стандартный WP REST API.  
**Минусы:** тема должна адекватно стилизовать сгенерированный HTML, или нужны классы под существующие стили.

**Порядок блоков в HTML (чередование — см. docs/landing-alternating-blocks.md):**
```
hero → for_whom_benefits (два в ряд) → gallery → features (текст+фото) → equipment (фото+текст) → pricing → booking_steps → form → cases → testimonials → faq
```

**Стили для блоков cases/testimonials (рекомендация):**
- `.landing-case-result` — акцент на результате (font-weight: 600 или цвет). B2B/коучинг-аудитория чаще цепляется за итог.

---

## 4. Рекомендуемый первый шаг: Вариант B

1. Добавить в `config/shared-config.json` маппинг slug → JSON для трёх страниц.
2. Реализовать `scripts/publish_konferenc_zal.py`:
   - чтение JSON
   - конвертация блоков в HTML
   - поиск/создание страницы по slug
   - обновление `post_content`

3. Проверить на одной странице (например, corporate_trainings).
4. При необходимости — перейти к Варианту A, если потребуется более гибкий рендеринг.

---

## 5. Что нужно на VPS (для Варианта B)

- Страницы в WP уже созданы вручную (или скрипт создаёт их при первом запуске).
- Шаблон «Лендинг Конференц-зал» при **непустом** `post_content` выводит только контент страницы (наш HTML); при пустом — статичный макет темы.
- Тема поддерживает классы из скрипта: `.landing-hero`, `.landing-row-two-cols`, `.landing-text-image`, `.landing-image-text`, `.landing-gallery`, `.landing-pricing` и т.д. (стили в `landing-pages.css`).

---

## 6. Связанные файлы

| Файл | Назначение |
|------|------------|
| `scripts/publish_konferenc_zal.py` | **Скрипт публикации** JSON → HTML → WP (hero, for_whom, benefits, features, pricing, equipment, booking_steps, form, gallery, testimonials, faq) |
| `docs/konferenc-zal-*.json` | JSON‑шаблоны |
| `prompts/konferenc-zal-rewrite.md` | Промпт для LLM |
| `docs/konferenc-zal-json-protocol.md` | Протокол |
| `seo-agents/agent4_publish/agent_4_publish.py` | Референс: WP API, авторизация, создание страниц |

---

## 7. Быстрый старт

```bash
# Только сгенерировать HTML (без отправки)
python scripts/publish_konferenc_zal.py --output-html

# Dry-run (проверка без запросов)
python scripts/publish_konferenc_zal.py --dry-run

# Публикация одной страницы
python scripts/publish_konferenc_zal.py korporativnye-treningi

# Все 3 страницы
python scripts/publish_konferenc_zal.py
```

---

## 8. Проверка реализации

| Проверка | Где смотреть |
|----------|---------------|
| Порядок и чередование блоков | `docs/landing-zaly-wireframe.md` — таблица «Порядок секций (конференц-зал, из скрипта)»; `docs/landing-alternating-blocks.md` |
| Классы HTML, генерируемые скриптом | `scripts/publish_konferenc_zal.py` — константа `SECTIONS_ORDER`, функция `_render_section()` |
| Шаблон WP выводит контент скрипта | Тема: `template-page-landing-konferenc-zal.php` — при непустом `post_content` выводится `the_content()` в `.landing__content-from-editor` |
| Стили двух колонок и текст/фото | Тема: `assets/css/landing-pages.css` — блок «Чередование блоков» в конце файла |
| Конфиг slug → JSON, шаблон страницы | `config/shared-config.json` — `konferenc_zal_pages`, `_page_template`: `template-page-landing-konferenc-zal.php` |
