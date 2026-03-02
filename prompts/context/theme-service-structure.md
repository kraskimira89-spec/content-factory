# Структура страницы услуги (entuziastov75-vps)

Контекст для агента-implementer: где и как реализованы блоки эталона.

## Шаблон и данные

- **Шаблон:** `wp-content/themes/entuziastov75-child/template-page-service.php` — один шаблон для всех услуг.
- **Выбор услуги:** по `post_name` (slug страницы WP): `uglekislaya-vanna`, `vlok`, `solyanaya-komnata` и т.д.
- **Данные:** `inc/service-pages-defaults.php` — PHP-массив `entuziastov75_get_service_defaults_extra()` по ключу slug.
- **REST API:** POST `/wp-json/entuziastov75/v1/service-data/{slug}` — обновление faq, comparison, results, how_steps и т.д. (merge с дефолтами).
- **Контент:** `post_content` страницы WP + данные из `services_data` (title, subtitle, intro, list_left, list_right, price_*, how_steps, results, comparison, faq, audience, hero_badges).

## Маппинг slug ↔ услуга

Из `config/shared-config.json` → `services`: `uglekislaya-vanna` = «Углекислая ванна», `vlok` = «ВЛОК», `solyanaya-komnata` = «Соляная комната», `pressoterapiya` = «Прессотерапия» и т.д.

## Поля services_data (на slug услуги)

| Поле | Назначение |
|------|------------|
| title | H1 |
| subtitle | Подзаголовок Hero |
| intro | Вводный абзац |
| hero_badges | Маркеры-факты в Hero (массив строк) |
| list_left | Показания (массив) |
| list_right | Противопоказания (массив) |
| price_name, price_time, price_one, price_five | Стоимость |
| how_steps | Шаги «Как проходит» (массив строк) |
| results | Результаты курса (массив) |
| comparison | { headers, rows } — таблица «Почему наш центр» |
| faq | [ { q, a }, ... ] |
| audience | [ { title, text }, ... ] — блок «Для кого» (если есть) |

## Блоки в шаблоне (порядок)

1. Hero (service-page__hero) — H1, subtitle, hero_badges, 2 кнопки, фото
2. Контент (service-page__content) — intro, post_content
3. Для кого (service-page__for-whom) — audience или list_left как карточки
4. Как проходит (service-page__how) — how_steps, нумерованные шаги, фото справа
5. Результаты курса (service-results)
6. Показания и противопоказания (service-page__benefits)
7. Стоимость (service-page__prices)
8. Сравнение «Почему наш центр» (service-comparison)
9. FAQ (service-faq)
10. CTA
11. Лид-магнит
12. Связанные услуги + Ноябрянам (service-page__bottom-blocks)
13. Финальный CTA

## Файлы темы для правок

- `template-page-service.php` — HTML-структура блоков
- `assets/css/service-pages.css` — стили
- `inc/service-pages-defaults.php` — дефолтные данные (PHP)
- REST `service-data/{slug}` — обновление данных без правки PHP (через content-factory scripts/deploy_services_data.py или agent4)

## Где что править

| Задача | Где |
|--------|-----|
| Добавить hero_badges, audience | inc/service-pages-defaults.php или REST service-data |
| Новый блок в шаблоне | template-page-service.php |
| Стили блока | assets/css/service-pages.css |
| Текст контента (лид, H2) | post_content страницы WP (редактор или agent4) |
| FAQ, comparison, results | service-data (REST или inc) |
