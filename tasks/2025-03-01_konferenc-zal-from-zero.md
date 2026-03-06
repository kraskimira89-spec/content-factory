# Задача: Конференц-зал с нуля (цепочка агентов 1–9)

Дата: 2025-03-01  
Тип: content

## Исходный запрос

Удалить страницы конференц-залов на сайте. Делать всё с нуля: шаблон, цепочка агентов 1–9, стиль как на страницах услуг. Схема чередования блоков.

## Выполнено

- [x] Удалены 4 страницы через `scripts/delete_konferenc_zal_pages.py`
- [x] Схема чередования в `docs/landing-zaly-wireframe.md`
- [x] Шаблон `prompts/templates/konferenc_zal_page.md`
- [x] Промпты: `agent2_konferenc_zal.txt`, `agent3_konferenc_zal.txt`
- [x] Агенты 2 и 3 с флагом `--konferenc-zal`
- [x] `scripts/run_konferenc_zal_chain.py` — запуск цепочки 1→5
- [x] `scripts/publish_konferenc_zal_from_md.py` — MD→HTML, публикация в WP
- [x] Конфиг `konferenc_zal` в `shared-config.json`

## Схема чередования блоков

1. Два в ряд: Для кого | Преимущества
2. Картинка во всю ширину: Галерея
3. Картинка слева, текст справа: Характеристики
4. Текст слева, картинка справа: Оснащение
5. Текст во всю ширину: Тарифы, Как забронировать, форма, кейсы, отзывы, FAQ
6. Картинка во всю ширину: финальное фото

## Запуск

```bash
# Полная цепочка (агенты 1→5 + публикация)
python scripts/run_konferenc_zal_chain.py

# Только до агента 3
python scripts/run_konferenc_zal_chain.py --stop-after 3

# Начать с редактора (агент 4)
python scripts/run_konferenc_zal_chain.py --skip-to 4
```

## Связанные файлы

- content-factory: `prompts/templates/konferenc_zal_page.md`, `prompts/agents/agent2_konferenc_zal.txt`, `prompts/agents/agent3_konferenc_zal.txt`
- Тема: `template-page-landing-konferenc-zal.php`, `assets/css/landing-pages.css`
