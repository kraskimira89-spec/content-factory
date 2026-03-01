# Промпты и контекст Content Factory

Централизованное хранилище системных промптов, шаблонов и контекстных данных.

## Карта промптов

Все системные промпты — в `prompts/agents/`:

| Файл | Агент | Назначение |
|------|-------|-----------|
| `agent1_keywords.txt` | agent1_keywords | Генерация ключевых фраз |
| `agent_planner.txt` | agent_planner | Контент-план (JSON-формат) |
| `agent2_brief.txt` | agent2_brief | ТЗ для авторов с учётом архитектуры шаблона |
| `agent3_content.txt` | agent3_content | Копирайтинг: tone of voice, структура, SEO |
| `agent_editor.txt` | agent_editor | Редактура: медицинские нормы, стиль |
| — | agent4_publish | Программный (без промпта) |
| — | agent_publish_vk | Программный (без промпта) |
| — | agent_analyst | Программный (без промпта) |

## Структура

```
prompts/
├── agents/                         ← системные промпты агентов
│   ├── agent1_keywords.txt
│   ├── agent2_brief.txt
│   ├── agent3_content.txt
│   ├── agent_editor.txt
│   └── agent_planner.txt
├── context/                        ← общий контекст бренда
│   ├── brand_voice.md
│   └── services.json
└── templates/                      ← шаблоны контента
    └── service_page.md
```

## Использование в агентах

```python
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent1_keywords.txt")
```

## Принципы

- Промпты хранятся **только здесь** — единственный источник истины
- Агенты загружают промпты через `PROMPT_FILE` → `load_system_prompt()`
- Контекстные файлы (`context/`) можно подмешивать в system/user prompt
- Изменения в промптах применяются при следующем запуске агента

## Синхронизация с VPS-проектом

Файлы конфигурации должны быть **идентичны** в обоих проектах:

- `content-factory` (источник)
- `entuziastov75-vps` (копия)

Пути на VPS: см. `docs/vps-paths.md`

### Что синхронизировать

| Файл | Назначение |
|------|------------|
| `config/shared-config.json` | Контракт: эндпоинты, рубрики, услуги, маппинги |
| `prompts/context/` | brand_voice.md, services.json |
| `docs/error-handling.md` | Описание retry-логики Agent 4 |

### Порядок при изменении

1. Редактировать в **content-factory**
2. Копировать в **entuziastov75-vps**
3. Коммитить в оба репо с одинаковым сообщением

### Проверка синхронности

```bash
# Из папки entuziastov75-vps
diff ../content-factory/config/shared-config.json ./config/shared-config.json
diff -r ../content-factory/prompts/context/ ./prompts/context/
```
