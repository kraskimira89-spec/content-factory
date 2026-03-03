# Миграция: services_slugs → uslugi в shared-config

Дата: 2025-03-01
Тип: code_vps

## Изменения в контракте (content-factory)

- **services** — только 6 услуг: Долголетие, Конференц-зал, Мастер Клёпа, Прокат, Юридическая помощь, Тренажёрный зал
- **uslugi** — 10 услуг под /uslugi/: gidromassazh, nastolnyy-tennis, solyanaya-komnata, fitobochka, massazh, pressoterapiya, vlok, uglekislaya-vanna, lfk, limfodrenazh-nog
- **services_slugs** — удалён, заменён на **uslugi** (объект slug → { name, aliases })

## Действия на VPS (entuziastov75-vps)

1. **Синхронизировать** shared-config.json из content-factory
2. **Проверить тему**: если PHP читает `services_slugs` (список), заменить на:
   - `array_keys($config['uslugi'])` — список slug'ов под /uslugi/
   - или `$config['uslugi']` — объект с полными данными (name, aliases)
3. **Обновить** inc/service-pages-defaults.php и REST service-data, если они завязаны на старый формат

## Файлы для проверки

- `www/entuziastov75.ru/wp-content/themes/flavor/inc/service-pages-defaults.php`
- Любые PHP-файлы, использующие `shared-config` или `services_slugs`
