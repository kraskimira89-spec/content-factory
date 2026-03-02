# Агенты проверки и доработки страницы услуги

Три агента в цепочке: **checker** → **executor** → **implementer**.

| Агент | Роль |
|-------|------|
| agent_checker | Проверяет страницу по 11 блокам → таблица + рекомендации |
| agent_checker_executor | По отчёту checker → ТЗ по тексту и верстке |
| agent_checker_implementer | По ТЗ → конкретные правки в теме/админке |

## Цепочка

1. **checker** — анализ страницы, чек-лист.
2. **executor** — ТЗ для копирайтера и верстальщика.
3. **implementer** — список изменений по файлам темы + действия в админке.

---

## Агент 1: checker

Проверяет страницу по эталонному чек-листу. Выход: таблица блоков (есть/нет/частично) + рекомендации.

```bash
python seo-agents/agent_checker/agent_checker.py -s "ВЛОК" -u http://91.229.11.147/uslugi/vlok/ -o output/check_vlok.md
python seo-agents/agent_checker/agent_checker.py -s "Углекислая ванна" -f materials/pages_manual/uglekislaya-vanna.md -o output/check_uglekislaya.md
```

| Параметр | Описание |
|----------|----------|
| `--service`, `-s` | Название услуги |
| `--file`, `-f` | Файл с HTML/текстом |
| `--url`, `-u` | URL страницы |
| `--audience`, `-a` | Подсказка по ЦА |
| `--output`, `-o` | Сохранить отчёт |

---

## Агент 2: executor

По отчёту checker формирует ТЗ по тексту и верстке.

```bash
# После checker
python seo-agents/agent_checker_executor/agent_checker_executor.py -s "Углекислая ванна" -r output/check_uglekislaya.md -o output/tz_uglekislaya.md

# С контекстом страницы (для указания конкретных мест)
python seo-agents/agent_checker_executor/agent_checker_executor.py -s "ВЛОК" -r output/check_vlok.md -p materials/pages_manual/vlok.md -o output/tz_vlok.md

# Пайп (checker → executor)
python seo-agents/agent_checker/agent_checker.py -s "Массаж" -u http://... -o - 2>/dev/null | python seo-agents/agent_checker_executor/agent_checker_executor.py -s "Массаж" --stdin -o output/tz_massazh.md
```

| Параметр | Описание |
|----------|----------|
| `--service`, `-s` | Название услуги |
| `--report`, `-r` | Файл с отчётом checker |
| `--page`, `-p` | Текст/HTML страницы (опционально) |
| `--stdin` | Читать отчёт из stdin |
| `--output`, `-o` | Сохранить ТЗ |

---

## Агент 3: implementer

По ТЗ executor формирует конкретные правки: какой файл изменить, какой код добавить, что вбить в админку.

```bash
python seo-agents/agent_checker_implementer/agent_checker_implementer.py -s "Углекислая ванна" -t output/tz_uglekislaya.md -o output/impl_uglekislaya.md

# По URL
python seo-agents/agent_checker_implementer/agent_checker_implementer.py -u /uslugi/vlok/ -t output/tz_vlok.md -o output/impl_vlok.md

# По slug
python seo-agents/agent_checker_implementer/agent_checker_implementer.py --slug uglekislaya-vanna -t output/tz_uglekislaya.md
```

| Параметр | Описание |
|----------|----------|
| `--service`, `-s` | Название услуги |
| `--url`, `-u` | URL страницы (извлекается slug) |
| `--slug` | Slug услуги (uglekislaya-vanna) |
| `--tz`, `-t` | Файл с ТЗ от executor |
| `--stdin` | Читать ТЗ из stdin |
| `--output`, `-o` | Сохранить результат |

**Выход:** изменения по файлам (template-page-service.php, inc/, CSS) + действия в админке + проверка эталона.

---

## Полный сценарий

```bash
# 1. Проверка
python seo-agents/agent_checker/agent_checker.py -s "Углекислая ванна" -u http://91.229.11.147/uslugi/uglekislaya-vanna/ -o output/check_uglekislaya.md

# 2. ТЗ
python seo-agents/agent_checker_executor/agent_checker_executor.py -s "Углекислая ванна" -r output/check_uglekislaya.md -o output/tz_uglekislaya.md

# 3. Правки в теме
python seo-agents/agent_checker_implementer/agent_checker_implementer.py -s "Углекислая ванна" -t output/tz_uglekislaya.md -o output/impl_uglekislaya.md

# 4. Применить правки из output/impl_uglekislaya.md в entuziastov75-vps
```

---

## Эталонные блоки (11)

1. Hero — H1, подзаголовок, CTA, краткие факты  
2. Для кого эта услуга  
3. Что даёт услуга  
4. Как проходит процедура  
5. Результаты курса  
6. Показания и противопоказания  
7. Стоимость  
8. Почему именно наш центр  
9. FAQ  
10. Связанные услуги / спецпредложение  
11. Финальный CTA  

## Формат вывода executor

1. **ТЗ по тексту** — задачи для копирайтера по блокам.
2. **ТЗ по верстке** — задачи для кодера (добавить блок, переверстать, тип компонента).
3. **Приоритеты** — 3–5 задач с высшим приоритетом.
