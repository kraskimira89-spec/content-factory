# Промпты и контекст Content Factory

## Карта промптов

Системные промпты хранятся **рядом с агентами** (единственный источник истины):

| Агент | Промпт | Назначение |
|-------|--------|-----------|
| agent1_keywords | `seo-agents/agent1_keywords/system_prompt.txt` | Генерация ключевых фраз |
| agent_planner | `seo-agents/agent_planner/system_prompt.txt` | Контент-план (JSON-формат) |
| agent2_brief | `seo-agents/agent2_brief/system_prompt.txt` | ТЗ для авторов с учётом архитектуры шаблона |
| agent3_content | `seo-agents/agent3_content/system_prompt.txt` | Копирайтинг: tone of voice, структура, SEO |
| agent_editor | `seo-agents/agent_editor/system_prompt.txt` | Редактура: медицинские нормы, стиль |
| agent4_publish | — (программный) | Публикация в WP REST API |
| agent_publish_vk | — (программный) | Анонс в ВК |
| agent_analyst | — (программный) | Пересчёт приоритетов |

## Эта папка: вспомогательные материалы

```
prompts/
├── context/
│   ├── brand_voice.md      — Тон коммуникации бренда
│   └── services.json       — Услуги: цены, длительность, категории
└── templates/
    └── service_page.md     — Шаблон структуры страницы услуги
```

## Использование в агентах

```python
PROMPTS_DIR = PROJECT_ROOT / "prompts"
brand_voice = (PROMPTS_DIR / "context" / "brand_voice.md").read_text("utf-8")
```

Контекстные файлы можно подмешивать в system prompt или передавать как user-контекст.

## Принцип

- **Промпты агентов** → `seo-agents/*/system_prompt.txt` (не дублировать!)
- **Общий контекст** (brand voice, услуги) → `prompts/context/`
- **Шаблоны вывода** → `prompts/templates/`
