# Тестирование интеграции content-factory ↔ WordPress

**Текущее состояние:** Agent 4 использует **стандартный WP REST API** (`/wp-json/wp/v2/`), а не кастомные эндпоинты.

---

## Шаг 0: Application Password

1. Открыть: http://91.229.11.147/wp-admin/profile.php
2. Секция "Application Passwords" → создать пароль (Name: `content-factory`)
3. Скопировать пароль (формат: `xxxx xxxx xxxx xxxx xxxx xxxx`)
4. Проверить `config/.env`:

```
WP_URL=http://91.229.11.147
WP_USERNAME=ваш_логин_wp
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

---

## Тест 1: Curl — проверка страницы (стандартный WP API)

```bash
# Проверить, существует ли страница по slug (Basic Auth)
curl -s -u "USERNAME:APP_PASSWORD" \
  "http://91.229.11.147/wp-json/wp/v2/pages?slug=gidromassazh&per_page=1"
```

Ожидаемый результат: JSON-массив (пустой `[]` если нет, или объект страницы).

---

## Тест 2: Curl — создание тестового поста (стандартный WP API)

```bash
curl -X POST "http://91.229.11.147/wp-json/wp/v2/posts" \
  -u "USERNAME:APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест из content-factory",
    "content": "<p>Тестовый контент.</p>",
    "status": "draft"
  }'
```

Ожидаемый результат: `{"id": 123, "link": "http://...", ...}`

---

## Тест 3: Запуск Agent 4

### Режимы запуска

| Команда | Поведение |
|---------|-----------|
| `python seo-agents\agent4_publish\agent_4_publish.py` | Берёт **последний** файл `*_page_*.md` |
| `python seo-agents\agent4_publish\agent_4_publish.py pressoterapiya` | Ищет файл с услугой **pressoterapiya** |

Формат имени файла: `{timestamp}_page_{Услуга}_{Город}.md` (например, `page_Прессотерапия_Ноябрьск.md`).

### Запуск

```powershell
cd D:\content-factory
call venv\Scripts\activate.bat
python seo-agents\agent4_publish\agent_4_publish.py pressoterapiya
```

### Ожидаемый вывод

```
=== Агент 4: публикация в WordPress ===
Используется файл (по slug «pressoterapiya»): ...\output\..._page_Прессотерапия_Ноябрьск.md
Услуга: Прессотерапия, город: Ноябрьск
...
✅ Страница обновлена: ID=35, link=...
```

---

## Тест 4: Полная цепочка (run_agents.bat)

```powershell
cd D:\content-factory
.\run_agents.bat
```

Запускает агентов 1→2→3→4 по очереди. Agent 1 запросит услугу и город вводом с клавиатуры.

---

## Тест 5: deploy_to_vps (service-data API)

Стандартный API для данных услуг: `/wp-json/entuziastov75/v1/service-data/{slug}`

```powershell
python scripts/deploy_to_vps.py --mode rest --dry-run
python scripts/deploy_to_vps.py --mode rest --slug gidromassazh
```

---

## Логи

| Где | Путь |
|-----|------|
| Agent 4 (если настроен) | `logs/seo_agents.log` или `output/logs/` |
| WordPress (на VPS) | `wp-content/debug.log` |

---

## Troubleshooting

| Ошибка | Решение |
|--------|---------|
| HTTP 401 | Проверить Application Password в .env |
| `Нет файлов *_page_*.md` | Сначала запустить Agent 3 (или цепочку 1→2→3) |
| `Slug не найден` | Проверить shared-config.json → services (name + aliases) |
| ConnectionError | Проверить доступность VPS: `ping 91.229.11.147` |

---

## Кастомный API (если будет добавлен на VPS)

Если на VPS создадут `inc/rest-api.php` с эндпоинтами:

- `POST /wp-json/custom/v1/publish-post`
- `GET /wp-json/custom/v1/post-status/{slug}`

то Agent 4 потребует доработки для переключения с `/wp/v2/` на `/custom/v1/`. Пока используется только стандартный WP REST API.
