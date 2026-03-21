# Паспорт проекта: Локальный контент‑завод на RTX 3060

## 1. Общая идея проекта

Создать локальную среду для генерации изображений и текстов на базе
NVIDIA RTX 3060 и ПК пользователя, чтобы:
- генерировать креативы, иллюстрации и визуал для SMM и маркетинга,
- запускать локальные LLM‑модели (через Ollama) для текстов, скриптов, анализа,
- в дальнейшем автоматизировать весь цикл через сценарии и интеграции.

## 2. Цели проекта

1. **Технические**
   - Настроить стабильную работу Stable Diffusion (SD 1.5 + при необходимости SDXL).
   - Настроить Ollama с CUDA/RTX для работы моделей DeepSeek и др.
   - Обеспечить безопасный разгон/охлаждение видеокарты для длительных задач.

2. **Прикладные**
   - Уметь локально генерировать серии изображений по шаблонам.
   - Уметь генерировать тексты/сценарии/описания через локальный LLM.
   - Подготовить фундамент для интеграции с таск‑менеджером/автоматизациями.

## 3. Техническая архитектура (текущая)

- **Железо**
  - CPU: Intel i7‑3820.
  - GPU: NVIDIA RTX 3060 12 GB.
  - RAM: 24 GB.
  - PSU: 800 W.

- **ПО**
  - ОС: Windows 10.
  - Драйвер NVIDIA: 551.74 (по выводу системы).
  - Python: 3.10.9 (user‑install).
  - Stable Diffusion WebUI (AUTOMATIC1111) v1.10.1, путь `D:\AI\stable-diffusion-webui`.
  - Базовая модель: `v1-5-pruned-emaonly.safetensors`.

- **Инструменты мониторинга**
  - MSI Afterburner (разгон/температура/кривые).
  - FurMark для стресс‑тестов.

## 4. План работ (этапы)

### Этап 1. Стабилизация и тест SD

- [x] Установка/настройка MSI Afterburner.
- [x] Стресс‑тест FurMark, фиксация температур.
- [x] Установка и запуск Stable Diffusion WebUI.
- [x] Подключение модели SD v1.5.
- [ ] Тестовый прогон: генерация 512×512 (кот, человек, предмет).
- [ ] Настройка параметров запуска (`--medvram`, `--opt-sdp-attention`).

### Этап 2. Подключение Ollama

- [ ] Установка Ollama под Windows.
- [ ] Проверка, что Ollama видит RTX 3060 (через `nvidia-smi`).
- [ ] Загрузка LLM‑модели (например, `deepseek-r1:8b`).
- [ ] Тест диалога и измерение нагрузки GPU/CPU.

### Этап 3. Рабочие сценарии

- [ ] Карточки товаров / рекламные креативы (SD).
- [ ] Генерация текстов/описаний (LLM).
- [ ] Склейка сценариев: один prompt → серия картинок + тексты.

### Этап 4. Автоматизация (долгосрочно)

- [ ] Обвязка через скрипты или n8n/Make.
- [ ] Интеграция с файловыми хранилищами/рассылками.
- [ ] Метрики: время генерации, стабильность, загрузка железа.

## 5. Ограничения и риски

- Ограниченный объём VRAM (12 GB) — осторожность с SDXL и большими LLM.
- Старый CPU может становиться узким местом при одновременных задачах.
- Необходимо регулярно мониторить температуры GPU.

## 6. Формат документации

- Технические шаги и команды фиксируются:
  - в `passport-conversation.md` (история действий и решений),
  - в `passport-project.md` (архитектура и план работ),
  - при необходимости — в отдельных `.md` для сценариев (workflow).

## 7. Ближайшие задачи

1. Подтвердить, что SD 1.5 генерирует изображения без ошибок.
2. Добавить в `webui-user.bat` оптимальные флаги запуска.
3. Установить и проверить Ollama с GPU.

---

## 8. Content Factory — текущая архитектура (дополнение 2026)

### Polyrepo

| Репозиторий | Стек | Назначение |
|-------------|------|------------|
| **content-factory** (этот) | Python 3.11+, PostgreSQL | Цепочка AI-агентов, генерация SEO-контента, публикация в WP |
| **entuziastov75-vps** | PHP, WordPress | Сайт на VPS: тема, шаблоны, REST-эндпоинты, service_data |

**Связь:** WordPress REST API + единый контракт `config/shared-config.json`.

### Цепочка агентов

```
agent1_keywords → agent_planner → agent2_brief → agent3_content → agent_editor
  → agent8_images_planner → agent9_images_runner → agent4_publish → agent_publish_vk → agent_analyst
```

Отдельно: **agent7_manual_publish** (ручные MD → WP), **agent_checker** → executor → implementer (проверка по чек-листу).

### Структура проекта

| Папка | Назначение |
|-------|------------|
| `seo-agents/` | Агенты: agent1–4, agent7, agent_planner, agent_editor, agent_checker*, agent_publish_vk, agent_analyst |
| `config/` | `.env` (секреты), `shared-config.json` (контракт с VPS) |
| `prompts/` | `agents/`, `context/`, `templates/` — промпты для агентов |
| `materials/pages_manual/` | Ручные MD-страницы услуг (slug из shared-config) |
| `output/` | Сгенерированный контент, `*_page_*.md` |
| `tasks/` | Файлы-задачи от Оркестратора |
| `scripts/` | deploy_to_vps, publish_konferenc_zal_from_md, run_konferenc_zal_chain, faq_parser |
| `docs/` | orchestrator-chat-prompt, landing-zaly-wireframe, vps-paths |

### Контракт shared-config.json (ключевые секции)

- **uslugi**, **services** — slug и name услуг (агент7, agent4)
- **konferenc_zal** — страница аренды зала (slug, шаблон, parent)
- **wordpress**, **endpoints** — WP URL, REST paths, service_data
- **sd_webui**, **comfyui** — генерация картинок (agent9)
- **deploy** — VPS paths, theme_child_path, theme_local_paths
- **rubrics** — категории блога, keywords

### Оркестратор

- Правило: `.cursor/rules/orchestrator.mdc`
- Паспорт для чата: `docs/orchestrator-chat-prompt.md`
- Workflow: `docs/orchestrator-workflow.md`
- Типы задач: content | code_vps | tz | mixed

### Генерация изображений (связь с локальным стеком)

- **agent8** — формирует промпты для картинок по структуре страницы
- **agent9** — отправляет запросы в SD WebUI (127.0.0.1:7860) или ComfyUI (часто 127.0.0.1:8000 в 0.15+)
- Конфиг: `shared-config.json` → `sd_webui` (checkpoint v1.5, 1280×720, negative_prompt)
- Хранение: `media/images/`, индекс в `db/image_index.json`

### Karusel: целевая среда GPU (фиксировано)

- **Целевой профиль окружения:** NVIDIA GPU (RTX 3060 12GB), Windows, Python 3.11.
- **Vision:** локальный Ollama (`VISION_BACKEND=ollama`, модель `llava`/`llava:13b`).
- **Rembg:** `onnxruntime-gpu` + CUDA 12.
- **Проверка провайдеров ONNX Runtime:**
  ```powershell
  python -c "import onnxruntime as ort; print(ort.get_available_providers())"
  ```
- **Подтверждённый статус:** `TensorrtExecutionProvider`, `CUDAExecutionProvider`, `CPUExecutionProvider`.
- Пошаговая инструкция по установке/восстановлению: `Karusel/docs/cuda12-rembg-gpu-windows.md`.

### Тема VPS (entuziastov75-child)

- **Репозиторий:** entuziastov75-vps (`C:\Users\user\Documents\seo_entuziastov75`), дочерняя тема в `wp-content/themes/entuziastov75-child/`.
- **Страницы услуг:** шаблон `template-page-service.php`, стили — `assets/css/service-pages.css` и `style.css`.
- **Зелёные CTA-блоки:** `.service-page__cta`, `.service-page__cta-text` (22px), `.service-page__cta-buttons` (flex, `justify-content: center`), вторая кнопка — контрастная (белый текст/рамка). Блок «Результаты курса» — `.results-cta` (кнопка по центру).
- **Деплой темы на VPS:** `python scripts/deploy_to_vps.py --mode theme` из content-factory (SCP в `/root/sites/entuziastov75VPS/www/entuziastov75.ru/wp-content/themes/entuziastov75-child/`).
- **Живой сайт (пример):** http://91.229.11.147/uslugi/massazh/

---

## 9. Ссылки для нового чата (сохранение контекста)

При старте нового чата подставь в первое сообщение ссылки на паспорта:

- **Паспорт проекта:** [Pasport_proekta/passport-project.md](Pasport_proekta/passport-project.md) — архитектура, polyrepo, агенты, контракт, тема VPS, SD.
- **Паспорт бесед:** [Pasport_besedy/passport-conversation.md](Pasport_besedy/passport-conversation.md) — история решений, команды, контекст Content Factory и последних бесед.
