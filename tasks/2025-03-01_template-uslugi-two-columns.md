# Задача: Двухколоночный шаблон страниц услуг
Дата: 2025-03-01
Тип: code_vps

## Исходный запрос
http://91.229.11.147/uslugi/fitobochka/ — страница должна быть в два столбца. Изменить шаблон страницы Услуг.

## Ответ от Мозга (Ask)
[не требуется]

## ТЗ для реализации

**Цель:** основной контент страницы услуги — в два столбца (текст слева, изображение/дополнение справа или grid 1fr 1fr).

### Где искать шаблон (entuziastov75-vps)

1. Тема: `www/.../wp-content/themes/flavor/`
2. Возможные файлы:
   - `page.php` — шаблон страницы по умолчанию
   - `page-uslugi.php` — кастомный шаблон для раздела «Услуги»
   - `single-service.php` или аналогичный
   - `template-parts/content-page.php` — вывод контента
3. Либо в `inc/` — логика/подключения

### Вариант правки (если контент в одной колонке)

Обернуть вывод `the_content()` в grid:

```php
<div class="service-page-content" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2em; align-items: start; max-width: 1200px; margin: 0 auto;">
  <div class="service-main">
    <?php the_content(); ?>
  </div>
  <div class="service-sidebar">
    <?php if ( has_post_thumbnail() ) : ?>
      <?php the_post_thumbnail( 'large' ); ?>
    <?php endif; ?>
    <!-- Доп. блоки: запись, связанные услуги и т.д. -->
  </div>
</div>
```

Либо, если нужен полноценный grid внутри контента (как в pressoterapiya):
- контент уже содержит `<div style="display: grid; grid-template-columns: 1fr 1fr">` из materials/pages_manual
- fitobochka может быть сгенерирована без этих блоков — проверить `materials/pages_manual/fitobochka.md` (если есть)
- при отсутствии — добавить grid-блоки в контент страницы или в шаблон

### Рекомендуемый подход

1. **В теме (PHP):** задать двухколоночный layout для области контента страниц услуг.
2. **В content-factory:** материалы (pressoterapiya, limfodrenazh-nog) уже используют grid в HTML — при перепубликации блоки сохранятся.

## Статус
- [ ] Найти файл шаблона страницы услуг в entuziastov75-vps
- [ ] Добавить grid-обёртку для контента
- [ ] Проверить fitobochka, pressoterapiya на VPS

## Связанные файлы
- entuziastov75-vps: `www/.../wp-content/themes/flavor/` (page.php или page-uslugi.php)
- content-factory: `materials/pages_manual/*.md` (контент с grid уже есть для прессотерапии, лимфодренажа)
