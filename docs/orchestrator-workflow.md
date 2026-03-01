# Рабочий ритуал: чат-Оркестратор

## Минимальный цикл

1. **Создай чат** в Cursor с названием «🧭 Orchestrator».
2. **Первым сообщением** вставь паспорт роли из `docs/orchestrator-chat-prompt.md`.
3. **Пиши туда** любую новую идею или проблему — не переключайся на Perplexity или другой проект вручную.

## Что делает Оркестратор

| Твой запрос | Его действия |
|-------------|--------------|
| «Нужна структура страницы для новой услуги Х» | Создаёт `tasks/...md`, тип tz/mixed, формирует промпт для Perplexity |
| «Допиши блок FAQ для соляной» | Создаёт задачу, указывает `materials/pages_manual/solyanaya-komnata.md`, команду agent7 |
| «Обновить shared-config и синхронизировать с VPS» | Создаёт задачу code_vps, напоминает про `diff` между репо |
| «Переосмысли УТП для прессотерапии» | Запрашивает PPL, создаёт задачу, после ответа — обновляет промпты или страницу |

## После ответа Perplexity

1. Вернись в тот же чат.
2. Вставь ответ PPL в сообщение или скажи «вставь в задачу X».
3. Оркестратор разнесёт ТЗ на файлы и подскажет команды.

## Команды, которые Оркестратор подскажет

- `python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya` — черновик
- `python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya --publish` — публикация
- `python scripts/deploy_to_vps.py --mode rest` — деплой service_data на VPS
- `python scripts/faq_parser.py materials/pages_manual/pressoterapiya.md` — проверить FAQ
