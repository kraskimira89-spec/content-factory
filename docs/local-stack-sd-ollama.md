# Локальный стек: SD WebUI и Ollama

Инструкция по настройке локальной среды для генерации изображений (Stable Diffusion) и локальных LLM (Ollama) в рамках паспорта проекта Content Factory.

---

## SD WebUI (Stable Diffusion)

### Требования

- Windows с поддержкой GPU (NVIDIA)
- Python 3.10
- Git

### Установка

1. Скачайте [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) или используйте существующую установку (путь в `config/shared-config.json` → `sd_webui.root_default`).
2. Запустите `webui-user.bat` (или `webui.bat`).
3. При первом запуске загрузятся зависимости.

### Тестовый прогон 512×512

1. Откройте WebUI в браузере (по умолчанию `http://127.0.0.1:7860`).
2. Промпт: `a calm landscape, mountains, sunset, realistic photo`.
3. Параметры: **Width 512**, **Height 512**, Steps 20–28.
4. Нажмите Generate. Изображение должно создаться за 10–60 сек (зависит от GPU).

### Настройка webui-user.bat

При необходимости измените:

- `COMMANDLINE_ARGS` — например, `--xformers` для ускорения, `--medvram` при нехватке VRAM.
- Путь к Python, если используется другой интерпретатор.

### Интеграция с Content Factory

- Agent9 использует SD WebUI по адресу из `SD_WEBUI_URL` (по умолчанию `http://127.0.0.1:7860`).
- Конфиг: `config/shared-config.json` → `sd_webui`.
- Рекомендуемый размер для hero: 1280×720 (site) или 1200×630 (VK feed).

---

## Ollama

### Установка

1. Скачайте [Ollama](https://ollama.ai) для Windows.
2. Установите и запустите. Ollama создаёт сервис и доступна по умолчанию на `http://localhost:11434`.

### Проверка GPU

```bash
ollama run llama3.2 "Hello"
```

Если ответ пришёл за несколько секунд — GPU используется. Для проверки можно открыть диспетчер задач → «Производительность» → GPU.

### Загрузка модели deepseek-r1:8b

```bash
ollama pull deepseek-r1:8b
```

Модель ~4.7 GB. После загрузки можно тестировать:

```bash
ollama run deepseek-r1:8b "Кратко опиши преимущества сухой углекислой ванны"
```

### Использование

- API: `http://localhost:11434/api/generate` (POST, JSON).
- Для интеграции с Content Factory — отдельный агент или скрипт, использующий Ollama API вместо облачного провайдера.

---

## Порядок проверки (чек-лист)

| Шаг | Действие | Ожидаемый результат |
|-----|----------|---------------------|
| 1 | Запустить SD WebUI | Открывается http://127.0.0.1:7860 |
| 2 | Генерация 512×512 | Изображение создаётся |
| 3 | Установить Ollama | Служба запущена |
| 4 | `ollama pull deepseek-r1:8b` | Модель загружена |
| 5 | `ollama run deepseek-r1:8b "тест"` | Текстовый ответ |

---

## Ссылки

- [SD WebUI GitHub](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- [Ollama](https://ollama.ai)
- [Shared config](../config/shared-config.json) — пути и параметры по умолчанию
