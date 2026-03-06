# Протокол для агента: JSON‑шаблоны конференц‑зала

**Назначение:** правила для LLM‑агента, который генерирует новые версии лендинга под ЦА или A/B‑тесты.

---

## 1. Поля, которые агент МОЖЕТ менять

| Блок | Поля | Комментарий |
|------|------|-------------|
| **meta** | `audience`, `version` | Менять при создании новой версии под ЦА |
| **meta_title** | — | SEO‑заголовок, адаптировать под запрос и ЦА |
| **meta_description** | — | SEO‑описание, до ~160 символов |
| **h1** | — | Главный заголовок страницы |
| **hero** | `title`, `subtitle`, `price_line`, `cta_primary`, `cta_secondary` | Полностью переписывать под ЦА |
| **for_whom** | Массив `{ title, text }` | Карточки сценариев, 4–5 шт. |
| **benefits** | Массив `{ title, text }` | Карточки преимуществ, 4–5 шт. |
| **pricing** | `description` в каждом тарифе | Описания можно адаптировать; `price` — по факту |
| **booking_steps** | Строки массива | Формулировки шагов |
| **form** | `title`, `description`, `fields[].label`, `submit_text` | Под ЦА |
| **gallery** | `title`, `description` | Подписи к фото |
| **testimonials** | `text`, `author`, `company` | Мини‑отзывы 2–4 строки: задача → как прошло → результат |
| **cases** | `title`, `client`, `goal`, `result` | Кейсы мероприятий: кто → что делали → результат |
| **faq** | Массив `{ question, answer }` | Вопросы и ответы, 5–7 пар |

---

## 2. Поля, которые агент НЕ меняет (структура)

| Элемент | Правило |
|---------|---------|
| **Ключи JSON** | Имена ключей (`hero`, `for_whom`, `benefits` и т.д.) не менять |
| **Порядок блоков** | hero → for_whom → benefits → features → pricing → equipment → booking_steps → form → gallery → cases → testimonials → faq |
| **Структура объектов** | `hero` всегда объект с `title`, `subtitle`, `price_line`, `cta_primary`, `cta_secondary` |
| **meta** | `page_type`, `locale`, `city` — константы |
| **slug** | `konferenc-zal` — не менять |
| **form.id** | `bron` — якорь для кнопки Hero |
| **features** | Массив `{ label, value }` — факты (площадь, вместимость и т.д.) |
| **equipment** | Список оборудования — факт, не маркетинг |

---

## 3. Ограничения по тону и стилю

- **Деловой тон** — без разговорного сленга и панибратства
- **Без «кричащих» обещаний** — избегать «лучший», «№1», «гарантированно», «революция»
- **Конкретика** — цифры (72 м², 40 человек, 500 ₽), факты, а не общие фразы
- **Геолокация** — упоминать «Ноябрьск» и «центр «Энтузиаст»» в hero и meta
- **Длина** | hero.subtitle — до 2 предложений; карточки for_whom/benefits — 1–2 предложения

---

## 4. Входные данные для агента

При генерации новой версии агенту передаётся:
- **audience** — целевая аудитория (corporate_trainings, online_schools, coaches_consultants или новая)
- **accents** — акценты (напр. «интернет, трансляции» для онлайн‑школ)
- **base_json** — путь к базовому шаблону

Агент возвращает JSON той же структуры с изменёнными текстами.

---

## 5. Промпт для LLM

Инструкция для локального агента: `prompts/konferenc-zal-rewrite.md`.

---

## 6. Файлы‑шаблоны

| Файл | audience |
|------|----------|
| `konferenc-zal-template.json` | general |
| `konferenc-zal-corporate-training.json` | corporate_trainings |
| `konferenc-zal-online-school.json` | online_schools |
| `konferenc-zal-coaches.json` | coaches_consultants |
