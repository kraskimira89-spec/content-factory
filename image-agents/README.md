# Image Agents — цепочка агентов картинок

Генерация промптов, вызов локального генератора изображений и прикрепление картинок при публикации. Точка подключения: после текстовых агентов (agent3), до публикации в WordPress (agent4/7).

## Цепочка (два варианта)

**Вариант A — агенты 8 и 9:**
1. **agent8_prompt** — по тексту поста + метаданным (услуга, аудитория, тон) генерирует JSON: `prompts`, `style`, `safety_notes`, `suggested_alt_texts`. Промпт: `prompts/agent_images_system.txt`.
2. **agent9_executor** — принимает один промпт, отправляет в локальный движок (`image_generator_url`), сохраняет в `media/images/YYYY/MM/slug-uuid.jpg`, возвращает `{ image_path, alt }`.
3. Регистрация в индексе (`scripts/image_repository.py`, `db/image_index.json`) — по желанию вызывается после agent9 или отдельным store.

**Вариант B — прежняя цепочка (image_jobs):**
1. **agent_image_prompt** — ТЗ на картинки в `output/image_jobs/{post_id}.json`.
2. **agent_image_job_sender** — джобы в очередь или на генератор.
3. **agent_image_store** — сканирует `output/images/`, добавляет записи в индекс.

## Публикация (agent4/7)

- Перед публикацией: `get_hero_image(post_id)` → featured_media; `get_images(post_id)` → остальные картинки вставляются в контент после первого абзаца.
- Локальные файлы при необходимости загружаются в WP Media, в индекс пишется `wp_attachment_id`.
- Репозиторий: `scripts/image_repository.py` (load_index, save_index, add_entry, get_images, get_hero_image, set_attachment_id).

## Конфиг (config/shared-config.json)

Секция `image_agents`:

- `image_storage_path` — папка готовых картинок (по умолчанию `output/images`)
- `image_jobs_path` — папка JSON-джоб от агента prompt
- `image_queue_path` — папка очереди для генератора (если не HTTP)
- `image_index_path` — файл индекса (по умолчанию `db/image_index.json`)
- `image_generator_url` — URL локального генератора: **`http://127.0.0.1:8000/generate`** (Flask `scripts/image_generate_api.py`). Переопределение: `IMAGE_GENERATOR_URL` в `config/.env`. На порту 7860 у SD WebUI нет `/generate`, только `/sdapi/v1/txt2img`.
- `image_generator_timeout_sec` — таймаут HTTP-запроса

## Запуск

```bash
# Сгенерировать ТЗ на картинки (передать структуру поста из кода или скрипта)
python image-agents/agent_image_prompt/agent_image_prompt.py

# Разложить джобы в очередь (или --http для отправки на генератор)
python image-agents/agent_image_job_sender/agent_image_job_sender.py
python image-agents/agent_image_job_sender/agent_image_job_sender.py --http

# Зарегистрировать новые картинки в индексе
python image-agents/agent_image_store/agent_image_store.py
```

Промпт агента: `prompts/agents/agent_image_prompt.txt`.
