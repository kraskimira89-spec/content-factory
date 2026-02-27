# Общая БД Content Factory

PostgreSQL-схема для цепочки агентов: планировщик, writer, publish, analyst.

## Настройка

1. Создайте БД: `createdb content_factory`
2. В `config/.env` задайте `DATABASE_URL` или `POSTGRES_*`
3. Примените схему и сиды:
   ```bash
   psql -d content_factory -f db/schema.sql
   psql -d content_factory -f db/seed.sql
   ```

## Примеры SQL (цепочка агентов)

Файл `db/examples_workflow.sql` — справочные запросы для Planner, Writer, Editor, Publisher (WordPress + ВК) и Analyst: кампании, content_items, content_versions, publishing_log, content_metrics, пересчёт приоритетов.

## Модуль Python

```python
from db import get_connection, is_available

if is_available():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rubrics")
    ...
```
