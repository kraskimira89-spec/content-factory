# Паспорт беседы: локальный ИИ‑стек (RTX 3060, SD + Ollama)

**Ссылки для старта нового чата с контекстом:**  
→ [Паспорт проекта](../Pasport_proekta/passport-project.md) | [Паспорт беседы](../Pasport_besedy/passport-conversation.md) (этот файл)

---

## 1. Участники

- Клиент: (ФИО/ник) __________________
- Ассистент: Perplexity (AI‑помощник), роль — технический консультант и наставник по локальному ИИ.

## 2. Цели беседы

1. Безопасно установить и настроить:
   - разгон и андервольт RTX 3060 под постоянные нагрузки (SD, LLM),
   - Stable Diffusion WebUI (AUTOMATIC1111) под Windows,
   - Ollama с использованием GPU.
2. Сформировать рабочий пайплайн «локальный контент‑завод»:
   - генерация изображений (SD),
   - генерация текстов/кода (LLM в Ollama),
   - дальнейшая интеграция с другими инструментами.

## 3. Текущий статус на момент создания паспорта

- Железо:
  - Видеокарта: NVIDIA GeForce RTX 3060 (12 GB).
  - Блок питания: 800 Вт.
- Разгон / охлаждение:
  - MSI Afterburner установлен.
  - Настройки: Temp Limit ~75 °C, Power Limit 95 %, лёгкий андервольт ядра и разгон памяти.
  - FurMark‑стресс‑тест пройден: максимум ~71 °C, без артефактов и вылетов.
- ПО:
  - Python 3.10 установлен (C:\Users\user\AppData\Local\Programs\Python\Python310\).
  - Stable Diffusion WebUI (AUTOMATIC1111) клонирован в `D:\AI\stable-diffusion-webui`.
  - Виртуальное окружение venv создано на Python 3.10.
  - Внутренние репозитории (stable-diffusion-stability-ai, generative-models, k-diffusion, BLIP) успешно клонированы.
  - Модель `v1-5-pruned-emaonly.safetensors` скачана и размещена в `D:\AI\stable-diffusion-webui\models\Stable-diffusion`.
  - WebUI открывается по адресу `http://127.0.0.1:7860`.

## 4. Основные решения и договорённости

- Используем «мягкий» разгон с приоритетом стабильности и ресурса железа.
- Все критичные изменения (разгон, обновления драйверов/библиотек) делаем пошагово с тестами и фиксацией результатов.
- Stable Diffusion:
  - базовая модель — SD 1.5 (`v1-5-pruned-emaonly.safetensors`);
  - размер 512×512 как дефолт для тестов;
  - внимание к потреблению VRAM при последующем подключении SDXL.
- Ollama:
  - цель — запуск моделей LLM с использованием той же RTX 3060;
  - приоритет — стабильность и умеренное использование видеопамяти.

## 5. Формат работы

- Общение — короткие итерации «шаг → отчёт → следующий шаг».
- Все важные команды и пути фиксируются в этом паспорте и в «паспорт проекта».
- При смене крупного этапа (например, добавление SDXL, интеграция с n8n/Make) вносим обновления в паспорт.

## 6. История ключевых этапов (кратко)

1. Установка и настройка MSI Afterburner, андервольт и тест FurMark.
2. Настройка Python 3.10 и клонирование A1111 WebUI.
3. Исправление проблем с устаревшим репозиторием Stable Diffusion, ручное клонирование актуального форка.
4. Установка зависимостей, создание venv.
5. Скачивание и подключение модели SD v1.5.
6. Успешный запуск WebUI.

## 7. Следующие шаги (черновик)

1. Подтвердить успешную генерацию тестового изображения в SD (кот 512×512).
2. Добавить параметры запуска WebUI под 12 GB VRAM (`--medvram` и др.).
3. Установить и проверить Ollama с использованием GPU.
4. Проработать сценарии «контент‑завода» (связка SD + LLM).

---

## 8. Content Factory — текущий контекст (дополнение 2026)

### Участники и роли

| Роль | Инструмент | Назначение |
|------|------------|------------|
| Оркестратор | Cursor, чат «🧭 Orchestrator» | Единая точка входа: классификация задач, создание `tasks/*.md`, подсказки команд |
| Цепочка агентов | `seo-agents/`, Python | keywords → brief → content → editor → publish → VK → analyst |
| Ручная публикация | agent7_manual_publish | MD из `materials/pages_manual/` → WordPress (черновик/публикация) |
| Деплой | `scripts/deploy_to_vps.py` | Тема, service_data, REST API на VPS |
| Генерация картинок | agent9 + SD WebUI | Промпты от agent8 → SD на 127.0.0.1:7860 |

### Ключевые команды

```bash
# Ручная публикация страницы услуги (slug из shared-config.json)
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya
python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya --publish

# Деплой на VPS
python scripts/deploy_to_vps.py --mode rest   # service_data
python scripts/deploy_to_vps.py --mode theme # тема WordPress

# Конференц-зал (цепочка + публикация)
python scripts/run_konferenc_zal_chain.py
python scripts/publish_konferenc_zal_from_md.py

# Проверка FAQ
python scripts/faq_parser.py materials/pages_manual/pressoterapiya.md
```

### Ключевые пути

- **Контракт:** `config/shared-config.json` (услуги, рубрики, endpoints, deploy)
- **Ручные страницы:** `materials/pages_manual/{slug}.md` — slug из `uslugi`/`services` в shared-config
- **Промпты:** `prompts/agents/`, `prompts/context/brand_voice.md`, `prompts/templates/`
- **Задачи:** `tasks/YYYY-MM-DD_описание.md`
- **Паспорт Оркестратора:** `docs/orchestrator-chat-prompt.md`, `.cursor/rules/orchestrator.mdc`

### SD WebUI в контексте Content Factory

- agent9 генерирует картинки для страниц услуг через SD WebUI (порт 7860)
- Конфиг: `shared-config.json` → `sd_webui` (base_url, checkpoint, размеры, negative_prompt)
- Альтернатива: ComfyUI (часто порт 8000 в 0.15+; старые сборки — 8188)

---

## 9. Беседа: страницы услуг, зелёные CTA, деплой (март 2026)

### Цели

- В зелёных CTA-блоках на страницах услуг: **крупнее текст**, **кнопки по центру**.
- Устранить визуальное «невыравнивание»: вторая кнопка («Получить консультацию») была зелёной на зелёном фоне — сделана контрастной (белый текст и светлая рамка).

### Что сделано

| Где | Изменения |
|-----|-----------|
| **service-pages.css** | `.service-page__cta-text`: font-size 22px, line-height 1.4; `.service-page__cta-buttons`: `justify-content: center`; `.service-page__cta .btn--secondary-light`: цвет #fff, border rgba(255,255,255,.85), hover — полупрозрачный белый фон. |
| **style.css** | `.service-page__cta-text`: 22px, line-height 1.4; добавлен `.service-page__cta-buttons { justify-content: center }`; `.results-cta`: `justify-content: center`, `.results-cta .btn`: `flex: 0 0 auto` (кнопка «Записаться на курс» по центру). |
| **Деплой** | Тема выложена на VPS: `python scripts/deploy_to_vps.py --mode theme`. После деплоя — жёсткое обновление (Ctrl+F5) или инкогнито. |

### Проверка

- **URL страницы услуги:** http://91.229.11.147/uslugi/massazh/
- На сервере версия CSS с `filemtime` (например `?ver=1773846828`) — после деплоя подхватывается автоматически.
