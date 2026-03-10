# Задача: План реализации по аудиту Content Factory
Дата: 2025-03-10
Тип: mixed

## Исходный запрос
Подготовить файл tasks/2025-03-10_plan-audit-implementation.md в формате Оркестратора (с полями ТЗ, статус, связанные файлы) на основе аудита: Pasport_besedy, Pasport_proekta, scripts, prompts, output, materials.

## Ответ от Мозга (Ask)
[аудит выполнен в предыдущем диалоге]

## ТЗ для реализации

### Приоритет 1 — Контент флагманов (Prioritet_uslug)
1. Создать `materials/pages_manual/sukhaya-uglekislaya-vanna.md`
2. Создать `materials/pages_manual/gidromassazh.md`
3. Добавить блоки «Точность по услугам» в `prompts/context/brand_voice.md` (при необходимости)
4. Опубликовать: agent7 sukhaya-uglekislaya-vanna, agent7 gidromassazh

### Приоритет 2 — Закрыть задачи VPS
5. limfodrenazh-nog: проверить публикацию на VPS (REST + валидатор), проверить service-pages-defaults.php
6. template-uslugi-two-columns: найти шаблон страниц услуг в entuziastov75-vps, добавить grid, проверить fitobochka, pressoterapiya

### Приоритет 3 — Остальные услуги (по мере необходимости)
7. aromaterapiya → massazh → skrabirovanie → obertyvanie → nuga-best → fitobar → nastolnyy-tennis → lfk — создать materials/pages_manual/{slug}.md + agent7

### Приоритет 4 — Локальный стек (паспорт проекта)
8. SD: тестовый прогон 512×512, настройка webui-user.bat
9. Ollama: установка, проверка GPU, загрузка deepseek-r1:8b

### Приоритет 5 — Поддержка
10. Синхронизация shared-config при изменениях контракта
11. git sync (factory/vps) после завершения задач

## Статус
- [x] Аудит выполнен
- [x] План зафиксирован в задаче
- [x] Приоритет 1: sukhaya-uglekislaya-vanna.md
- [x] Приоритет 1: gidromassazh.md
- [x] Приоритет 1: brand_voice.md — блоки СУВ и Гидромассаж
- [x] Приоритет 1: agent7 sukhaya-uglekislaya-vanna — опубликовано (черновик)
- [x] Приоритет 1: agent7 gidromassazh — опубликовано (черновик)
- [x] Приоритет 2: limfodrenazh-nog — дефолты добавлены в inc/service-pages-defaults.php, скопировано на VPS по SCP
- [x] Приоритет 2: template-uslugi-two-columns — grid уже есть (entuziastov75_wrap_first_two_h2_sections_in_grid)
- [x] Приоритет 3: остальные страницы — aromaterapiya, massazh, skrabirovanie, obertyvanie, nuga-best, fitobar, nastolnyy-tennis, lfk (черновики в WP)
- [x] Приоритет 4: docs/local-stack-sd-ollama.md — инструкция SD + Ollama
- [ ] Приоритет 5: shared-config sync при изменениях
- Ручные действия: загрузить featured image для konferenc-zal; заполнить блок «Специальное предложение» для флагманов (СУВ, ВЛОК, Гидромассаж)

## Связанные файлы
- content-factory: materials/pages_manual/sukhaya-uglekislaya-vanna.md
- content-factory: materials/pages_manual/gidromassazh.md
- content-factory: prompts/context/brand_voice.md
- content-factory: config/shared-config.json
- content-factory: tasks/2025-03-01_limfodrenazh-nog.md
- content-factory: tasks/2025-03-01_template-uslugi-two-columns.md
- entuziastov75-vps: wp-content/themes/flavor/ (шаблон услуг)
- entuziastov75-vps: inc/service-pages-defaults.php

## Команды для запуска вручную

```bash
# Публикация флагманов (черновик)
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py sukhaya-uglekislaya-vanna
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py gidromassazh

# Сразу опубликовать (после проверки)
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py sukhaya-uglekislaya-vanna --publish
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py gidromassazh --publish
```
