# Подключение Google Sheets к content-factory

## Этап 2.2 → 2.3

Агенты читают очередь задач из листа **Queue** и пишут обратно `wp_page_id`, `wp_url`, меняют статус на `done`.

---

## 1. Сервисный аккаунт в Google Cloud

1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект или выберите существующий
3. **APIs & Services** → **Enable APIs** → включите **Google Sheets API**
4. **APIs & Services** → **Credentials** → **Create Credentials** → **Service account**
5. Укажите имя (например, `content-factory-sheets`), создайте
6. Нажмите на созданный аккаунт → вкладка **Keys** → **Add key** → **Create new key** → **JSON**
7. Скачайте JSON-файл и сохраните в безопасном месте (например, `config/google-sheets-credentials.json`)

---

## 2. Доступ к таблице

1. Откройте JSON-ключ, скопируйте значение `client_email` (типа `xxx@project-id.iam.gserviceaccount.com`)
2. Откройте [таблицу](https://docs.google.com/spreadsheets/d/1uL2BUXrN-E85s3OEz9DjzeT8rQouBpTQZOMjwUEmquo)
3. **Поделиться** → вставьте `client_email` → роль **Редактор** → **Готово**

---

## 3. Настройка .env

В `config/.env` добавьте:

```env
GOOGLE_APPLICATION_CREDENTIALS=config/google-sheets-credentials.json
```

(Путь относительно корня проекта или абсолютный.)

---

## 4. Структура листов

### Queue

| A (id) | B (slug)       | C (status) | D (planned_date) | E (topic_id) |
|--------|----------------|------------|------------------|--------------|
| Q001   | aromaterapiya  | done       |                  | T001         |
| Q002   | gidromassazh   | queue      | 10.03            | T002         |

### Services

| A (slug)      | B (wp_page_id) | C (category) | D (price) | E (wp_url) |
|---------------|----------------|--------------|-----------|------------|
| aromaterapiya | 123            | Массаж       | 800       | https://...|

Колонка **E (wp_url)** добавляется agent4 после публикации. Если её нет — создастся при первой записи.

---

## 5. Использование

```bash
# Агент 1: взять задачу из Queue (первую со status=queue)
python seo-agents\agent1_keywords\agent_1_keywords.py --from-queue

# Далее — цепочка planner → agent2 → agent3 → editor → agent8 → agent9 → agent4
# Agent4 после публикации автоматически обновит Services и Queue
```
