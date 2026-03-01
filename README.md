# Content Factory

Контент-завод — автоматизация создания и публикации SEO-контента для сайта **Энтузиаст** (Ноябрьск).

## Архитектура: polyrepo

| Репозиторий | Стек | Назначение |
|---|---|---|
| **content-factory** (этот) | Python, PostgreSQL | Цепочка AI-агентов, генерация контента, публикация |
| **entuziastov75-vps** | PHP, WordPress | Сайт на VPS: тема, шаблоны, REST-эндпоинты |

Связь между проектами — через **WordPress REST API** и единый контракт `config/shared-config.json`.

## Структура проекта

| Папка | Назначение |
|-------|------------|
| `seo-agents/` | Цепочка из 8 AI-агентов (keywords → plan → brief → content → edit → publish → VK → analyst) |
| `config/` | Единый `.env` (секреты), `shared-config.json` (контракт с VPS-сайтом) |
| `scripts/` | Скрипты автоматизации и деплоя |
| `db/` | PostgreSQL-схема для пайплайна агентов |
| `output/` | Сгенерированный контент (markdown, PHP-патчи) |
| `tasks/` | Файлы-задачи от Оркестратора (YYYY-MM-DD_описание.md) |
| `docs/` | Документация |
| `materials/` | Исходные материалы (PDF, DOCX — не в git) |

## Цепочка агентов

```
agent1_keywords → agent_planner → agent2_brief → agent3_content
    → agent_editor → agent4_publish → agent_publish_vk → agent_analyst
```

Запуск всей цепочки: `run_agents.bat`

## Оркестратор

Единая точка входа для задач: контент-завод, VPS-сайт, Perplexity (ТЗ/концепции).

1. Создай чат «🧭 Orchestrator» в Cursor
2. Первым сообщением вставь паспорт из `docs/orchestrator-chat-prompt.md`
3. Пиши туда новые идеи — он создаёт `tasks/*.md`, подсказывает команды, готовит промпты для PPL

Подробнее: `docs/orchestrator-workflow.md`

## Быстрый старт

1. Скопировать `config/.env.example` → `config/.env`, заполнить ключи
2. `pip install -r requirements.txt` (в venv)
3. `run_agents.bat` или запускать агентов по одному из `seo-agents/`
