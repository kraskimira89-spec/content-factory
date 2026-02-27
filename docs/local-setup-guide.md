# ТЕХНИЧЕСКИЙ ГАЙД: ЛОКАЛЬНАЯ УСТАНОВКА И АДАПТАЦИЯ ПО ДЛЯ КОНТЕНТ-ЗАВОДА

## ОГЛАВЛЕНИЕ

1. [Введение](#введение)
2. [Сравнительная таблица ПО](#сравнительная-таблица-по)
3. [Локальная установка LLM (DeepSeek/Ollama)](#локальная-установка-llm)
4. [Замена Make.com на n8n](#замена-makecom-на-n8n)
5. [Локальная генерация изображений](#локальная-генерация-изображений)
6. [Адаптация архитектуры проекта](#адаптация-архитектуры-проекта)
7. [Изменения в Workflow](#изменения-в-workflow)
8. [Конфигурационные файлы](#конфигурационные-файлы)
9. [Развертывание на Windows 10](#развертывание-на-windows-10)
10. [Troubleshooting](#troubleshooting)

---

## ВВЕДЕНИЕ

Данный гайд описывает, как заменить облачные платные сервисы из оригинальной стратегии на локальные или российские аналоги без потери функциональности контент-завода.

**Цели локализации:**
- Снижение ежемесячных затрат с $146 до $20-40
- Независимость от зарубежных сервисов (санкции, блокировки)
- Полный контроль над данными и процессами
- Возможность работы без интернета (для части операций)

**Системные требования (минимальные):**
- **ОС:** Windows 10 Pro (64-bit) с WSL2
- **CPU:** Intel Core i5 8-го поколения или AMD Ryzen 5 3600+
- **RAM:** 16 GB (рекомендуется 32 GB для локальных LLM)
- **GPU:** NVIDIA RTX 3060 12GB или выше (для Stable Diffusion и локальных LLM)
- **Диск:** 100 GB свободного места (SSD предпочтительно)
- **Интернет:** для API социальных сетей и облачных сервисов (YandexGPT, Google Sheets)

---

## СРАВНИТЕЛЬНАЯ ТАБЛИЦА ПО

### Полная таблица: Облачные сервисы vs Локальные/Российские аналоги

| № | Инструмент (из стратегии) | Тип | Локальная установка на Windows 10 | Российский/Открытый аналог | Совместимость с цепочками | Стоимость (месяц) | Рекомендация |
|---|---------------------------|-----|-----------------------------------|----------------------------|---------------------------|-------------------|--------------|
| **1. LLM и текстовые модели** |
| 1.1 | OpenAI GPT-4/5 | Облако (SaaS) | ❌ Нет | ✅ DeepSeek R1 (локально), YandexGPT 4 (облако РФ) | 🟢 Полная: JSON Chat Completion API | GPT: $40/мес → DeepSeek: $0, YandexGPT: ~$10/мес | **DeepSeek локально** (для конфиденциальности) или **YandexGPT** (для скорости) |
| 1.2 | Claude (Anthropic) | Облако (SaaS) | ❌ Нет | ✅ DeepSeek R1, GigaChat (Сбер) | 🟢 Полная: API паттерн идентичен | Claude: $30/мес → GigaChat: бесплатно до 50k токенов/мес | **GigaChat** (бесплатный лимит) или **DeepSeek** |
| 1.3 | Gemini (Google) | Облако (SaaS) | ❌ Нет | ✅ YandexGPT 4, DeepSeek | 🟢 Полная | Gemini: $20/мес → YandexGPT: $10/мес | **YandexGPT 4** |
| 1.4 | DeepSeek R1/V3 | Облако + Open Source | ✅ Да (WSL2, Ollama, LM Studio) | ✅ Сам является открытой моделью | 🟢 Полная: идентичный API | Облако: ~$5/мес, Локально: бесплатно | **Локально через Ollama** (см. секцию 3) |
| 1.5 | YandexGPT 4 | Облако (РФ) | ❌ Нет (только API) | ✅ YandexGPT - российский сервис | 🟢 Полная | ~$10/мес (до 1M токенов) | **Использовать как есть** (надежный РФ-сервис) |
| **2. Оркестрация и автоматизация** |
| 2.1 | Make.com | Облако (SaaS) | ❌ Нет self-hosted | ✅ n8n (self-hosted), Albato (РФ-облако) | 🟢 Высокая: концепция узлов идентична | Make: $16/мес → n8n: бесплатно (self-hosted), Albato: от 990₽/мес | **n8n (Docker)** для полного контроля (см. секцию 4) |
| **3. Генерация изображений** |
| 3.1 | DALL-E 3 (OpenAI) | Облако (SaaS) | ❌ Нет | ✅ Stable Diffusion XL, Kandinsky 3.1 (Сбер), Shedevrum (Яндекс) | 🟢 Высокая: промпт → изображение | DALL-E: $0.04-0.08/шт → SD: бесплатно | **Stable Diffusion XL локально** (см. секцию 5) |
| 3.2 | Midjourney | Облако (Discord) | ❌ Нет | ✅ Stable Diffusion, Kandinsky 3.1, Flux | 🟢 Высокая: текстовый промпт | Midjourney: $10-30/мес → SD: бесплатно | **Stable Diffusion + модель Realistic Vision** |
| 3.3 | Flux (Black Forest Labs) | Облако + Open Source | ✅ Частично (через ComfyUI) | ✅ Flux Dev - открытая модель | 🟢 Полная | Облако через Replicate: ~$0.03/шт, Локально: бесплатно | **Flux Dev через ComfyUI** (качество выше SD) |
| **4. Генерация видео** |
| 4.1 | Sora (OpenAI) | Облако (закрыт бета) | ❌ Нет | ⚠️ Нет полноценной замены. Частично: Kandinsky Video, Runway Gen-3 (облако) | 🟡 Средняя: API доступен у немногих | Sora: недоступно → Runway: $12/мес (лимиты) | **Runway Gen-3** (облако) или **Kling AI** |
| 4.2 | Kling AI | Облако (SaaS) | ❌ Нет | ✅ Доступен из РФ через VPN | 🟢 Полная | ~$10-20/мес | **Использовать как есть** (работает) |
| 4.3 | HeyGen (аватары) | Облако (SaaS) | ❌ Нет | ⚠️ Нет прямых аналогов. Частично: Synthesia, D-ID (облако) | 🟡 Средняя | HeyGen: $24/мес → Synthesia: $30/мес | **Не использовать** (дорого) или **генерировать без аватаров** |
| **5. Обработка медиа** |
| 5.1 | FFmpeg | Open Source | ✅ Да (нативно на Windows) | ✅ Уже открытый, аналогов не требуется | 🟢 Полная | Бесплатно | **Установить локально** (обязательно) |
| 5.2 | Whisper (OpenAI) | Облако + Open Source | ✅ Да (Whisper.cpp, Faster Whisper) | ✅ Открытая модель | 🟢 Полная | OpenAI API: $0.006/мин → Локально: бесплатно | **Faster Whisper локально** |
| 5.3 | Suno (музыка) | Облако (SaaS) | ❌ Нет | ⚠️ MusicGen (Meta, локально), Soundraw (облако) | 🟡 Средняя: качество ниже | Suno: $10/мес → MusicGen: бесплатно | **MusicGen локально** или стоковая музыка |
| **6. Хранение и базы данных** |
| 6.1 | Google Sheets | Облако | ❌ Нет (только через браузер/API) | ✅ Baserow (self-hosted), Airtable-аналоги | 🟡 Средняя: нужно переписать коннекторы | Google Sheets: бесплатно, Baserow: бесплатно | **Оставить Google Sheets** (удобство) или **Baserow** (приватность) |
| **7. Социальные сети (публикация)** |
| 7.1 | YouTube, Pinterest, TikTok | Облако (платформы) | ❌ Нет локальной замены | ✅ RuTube, Дзен, VK Видео (для РФ-аудитории) | 🟢 Полная: API-паттерны схожи | Бесплатно | **Диверсифицировать**: YouTube + RuTube + Дзен |
| 7.2 | Instagram, Facebook | Облако (Meta) | ❌ Нет | ✅ VK, Одноклассники (для РФ) | 🟢 Полная | Бесплатно | **VK + OK** (основной фокус для РФ-региона) |
| 7.3 | Telegram | Облако + API | ❌ Нет (только через API) | ✅ Telegram - нейтральная платформа | 🟢 Полная | Бесплатно | **Использовать как есть** |
| **8. Вспомогательные сервисы** |
| 8.1 | Perplexity | Облако (SaaS) | ❌ Нет | ✅ YandexGPT + Yandex Search API, локальный LLM + SerpAPI | 🟢 Высокая: поиск + генерация | Perplexity: $20/мес → Yandex: $5/мес | **YandexGPT + Yandex Search** |
| 8.2 | Quillbot, Monica (браузерные AI) | Облако (расширения) | ⚠️ Частично (локальные расширения) | ✅ Локальные LLM + Page Assist (расширение) | 🟡 Средняя | Quillbot: $10/мес → Локально: бесплатно | **Не критично для контент-завода** |

---

### Итоговая стоимость после локализации

| Компонент | Было (облако) | Стало (локально/РФ) | Экономия |
|-----------|---------------|---------------------|----------|
| LLM (GPT-4/5) | $40/мес | DeepSeek локально: $0 | -$40 |
| Make.com | $16/мес | n8n self-hosted: $0 | -$16 |
| DALL-E/Midjourney | $30/мес | Stable Diffusion: $0 | -$30 |
| Sora/Kling | $50/мес | Kling: $15/мес (меньше запросов) | -$35 |
| YandexGPT | $10/мес | YandexGPT: $10/мес (оставить) | $0 |
| **ИТОГО** | **$146/мес** | **$25/мес** | **-$121/мес (-83%)** |

**Дополнительные затраты (разовые):**
- GPU NVIDIA RTX 3060 (если нет): ~40,000₽ (разово)
- VPS для n8n (опционально): ~500₽/мес

---

## ЛОКАЛЬНАЯ УСТАНОВКА LLM

### Вариант 1: DeepSeek через Ollama (рекомендуется)

**Преимущества:**
- Простая установка (один установщик)
- Автоматическое управление моделями
- Совместимый OpenAI API endpoint
- Работает на CPU и GPU

**Шаги установки:**

#### 1. Установить Ollama на Windows

```powershell
# Скачать установщик с официального сайта
# https://ollama.com/download/windows

# Или через PowerShell (от имени администратора)
Invoke-WebRequest -Uri https://ollama.com/download/OllamaSetup.exe -OutFile OllamaSetup.exe
.\OllamaSetup.exe
```

#### 2. Скачать модель DeepSeek R1

```bash
# Открыть PowerShell/CMD
ollama pull deepseek-r1:7b
# Для более мощного варианта (требуется 32GB RAM):
ollama pull deepseek-r1:14b
```

**Размеры моделей:**
- `deepseek-r1:7b` — 4.3 GB (минимум 8GB RAM)
- `deepseek-r1:14b` — 8.6 GB (минимум 16GB RAM)
- `deepseek-r1:32b` — 20 GB (минимум 32GB RAM)

#### 3. Запустить локальный API-сервер

```bash
# Ollama автоматически запускает сервер на http://localhost:11434
# Проверить статус:
ollama list
```

#### 4. Тест API

```python
# test_ollama.py
import requests
import json

url = "http://localhost:11434/api/chat"

payload = {
    "model": "deepseek-r1:7b",
    "messages": [
        {
            "role": "system",
            "content": "Ты — эксперт по созданию контента для медицинских центров."
        },
        {
            "role": "user",
            "content": "Напиши короткий пост о пользе массажа для людей на Крайнем Севере."
        }
    ],
    "stream": False
}

response = requests.post(url, json=payload)
result = response.json()
print(result['message']['content'])
```

```bash
python test_ollama.py
```

#### 5. Интеграция в проект

**Обновить `.env` файл:**

```env
# Было:
# OPENAI_API_KEY=sk-proj-...
# OPENAI_API_URL=https://api.openai.com/v1

# Стало:
OLLAMA_API_URL=http://localhost:11434/api
OLLAMA_MODEL=deepseek-r1:7b
# Оставить YandexGPT для высокочастотных запросов:
YANDEX_GPT_API_KEY=...
```

**Обновить `scripts/content_generator.py`:**

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/chat')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'deepseek-r1:7b')

def generate_text_ollama(system_prompt, user_prompt):
    """
    Генерация текста через локальный Ollama API (DeepSeek).
    
    :param system_prompt: Системный промпт (контекст, роль)
    :param user_prompt: Пользовательский промпт (задача)
    :return: Сгенерированный текст
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        return result['message']['content']
    else:
        raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

# Пример использования:
if __name__ == '__main__':
    system = "Ты — SMM-менеджер для Центра здоровья на Крайнем Севере."
    user = "Создай короткий пост о пользе массажа (150-200 символов)."
    
    text = generate_text_ollama(system, user)
    print(text)
```

---

### Вариант 2: DeepSeek через LM Studio (GUI-интерфейс)

**Преимущества:**
- Графический интерфейс (удобнее для новичков)
- Встроенный чат для тестирования
- Автоматическая настройка GPU

**Шаги установки:**

#### 1. Скачать LM Studio

https://lmstudio.ai/

#### 2. Запустить LM Studio → Search Models → Найти "deepseek-r1"

#### 3. Скачать модель (например, `deepseek-r1-7b-GGUF`)

#### 4. Local Server → Start Server (порт: 1234)

#### 5. Тест API

API совместим с OpenAI, URL: `http://localhost:1234/v1`

```python
import openai

openai.api_key = "lm-studio"  # Любой ключ (не проверяется)
openai.api_base = "http://localhost:1234/v1"

response = openai.ChatCompletion.create(
    model="deepseek-r1-7b",
    messages=[
        {"role": "system", "content": "Ты — эксперт по контенту."},
        {"role": "user", "content": "Напиши короткий пост о массаже."}
    ],
    temperature=0.7
)

print(response['choices'][0]['message']['content'])
```

---

### Вариант 3: YandexGPT 4 (облако, но РФ)

**Преимущества:**
- Не требует мощного железа
- Хорошее понимание русского языка
- Низкая стоимость (~$10/мес до 1M токенов)

**Шаги настройки:**

#### 1. Создать аккаунт в Yandex Cloud

https://cloud.yandex.ru/

#### 2. Создать Folder (каталог)

Console → Create Folder → Название: "ContentFactory"

#### 3. Получить API-ключ

IAM Token или API Key:
- https://cloud.yandex.ru/docs/iam/operations/api-key/create

#### 4. Включить биллинг

Минимальный платеж: 1000₽ (~$10)

#### 5. Тест API

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_API_KEY = os.getenv('YANDEX_GPT_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

def generate_text_yandex(prompt, system_prompt="Ты — эксперт по контенту."):
    """
    Генерация текста через YandexGPT 4 API.
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return result['result']['alternatives'][0]['message']['text']
    else:
        raise Exception(f"YandexGPT error: {response.status_code} - {response.text}")

# Пример:
if __name__ == '__main__':
    text = generate_text_yandex("Напиши короткий пост о пользе массажа.")
    print(text)
```

**Обновить `.env`:**

```env
YANDEX_GPT_API_KEY=AQVNxxxxxxxxxx
YANDEX_FOLDER_ID=b1gxxxxxxxxxx
```

---

### Сравнение вариантов LLM

| Критерий | Ollama (DeepSeek) | LM Studio (DeepSeek) | YandexGPT 4 |
|----------|-------------------|----------------------|-------------|
| **Стоимость** | Бесплатно | Бесплатно | ~$10/мес |
| **Требования железа** | 16GB RAM, GPU желательна | 16GB RAM, GPU желательна | Нет (облако) |
| **Скорость генерации** | Средняя (зависит от GPU) | Средняя | Быстро |
| **Качество (русский)** | Хорошее | Хорошее | Отличное |
| **Приватность** | 100% локально | 100% локально | Облако (РФ) |
| **Сложность настройки** | Низкая | Очень низкая | Средняя |
| **Рекомендация** | ✅ Основной вариант | ✅ Для новичков | ✅ Для масштаба |

**Итоговая рекомендация:**
- **Для разработки и тестирования:** Ollama (DeepSeek R1:7b)
- **Для продакшена:** Гибрид — 70% Ollama (экономия) + 30% YandexGPT (критичные задачи, высокое качество)

---

## ЗАМЕНА MAKE.COM НА N8N

### Что такое n8n?

**n8n** — open-source аналог Make.com/Zapier с:
- Визуальным конструктором workflow (drag-and-drop)
- 400+ встроенных интеграций
- Self-hosted развертыванием (Docker, VPS, локально)
- Совместимым API (HTTP, Webhook, JavaScript)

**Официальный сайт:** https://n8n.io/

---

### Установка n8n на Windows 10

#### Вариант 1: Docker Desktop (рекомендуется)

**Шаг 1: Установить Docker Desktop**

https://www.docker.com/products/docker-desktop/

**Шаг 2: Создать `docker-compose.yml`**

```yaml
# docker-compose.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_secure_password_here
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=Europe/Moscow
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

**Шаг 3: Запустить n8n**

```bash
# В папке с docker-compose.yml:
docker-compose up -d

# Проверить статус:
docker ps

# Открыть в браузере:
http://localhost:5678
```

**Логин:**
- Username: `admin`
- Password: `your_secure_password_here`

---

#### Вариант 2: Установка через npm (без Docker)

**Требования:**
- Node.js 18+ (https://nodejs.org/)

```bash
# Установить n8n глобально:
npm install n8n -g

# Запустить:
n8n start

# Открыть:
http://localhost:5678
```

---

### Миграция workflow из Make.com в n8n

#### Шаг 1: Экспорт workflow из Make.com

1. Открыть Make.com → Scenarios
2. Выбрать workflow → три точки → Export blueprint (JSON)
3. Сохранить файл `workflow_1_seo_articles.json`

#### Шаг 2: Анализ структуры Make.com workflow

Make.com использует структуру:
- **Modules** — блоки (триггеры, действия)
- **Connections** — линии связи между модулями
- **Mapping** — передача данных между модулями

n8n использует аналогичную структуру:
- **Nodes** — блоки (аналог Modules)
- **Connections** — связи
- **Expressions** — передача данных (`{{ $json.field }}`)

#### Шаг 3: Создать аналогичный workflow в n8n

**Пример: Workflow #1 (SEO-статьи)**

**Make.com структура:**
```
[Schedule Trigger] → [Google Sheets: Get Row] → [YandexGPT] → [OpenAI: GPT-4] → [DALL-E] → [Google Sheets: Update] → [WordPress: Create Post]
```

**n8n структура (аналог):**

1. **Создать новый workflow в n8n**

2. **Добавить Cron Node (триггер по расписанию):**
   - Node: `Cron`
   - Mode: Every 2 days at 10:00
   - Timezone: Europe/Moscow

3. **Добавить Google Sheets Node (чтение данных):**
   - Node: `Google Sheets`
   - Operation: Get Rows
   - Document ID: (из `.env`)
   - Sheet Name: `Темы контента`
   - Return All: No
   - Limit: 1
   - Filters:
     - Column: `Статус`
     - Value: `черновик`

4. **Добавить HTTP Request Node (YandexGPT):**
   - Node: `HTTP Request`
   - Method: POST
   - URL: `https://llm.api.cloud.yandex.net/foundationModels/v1/completion`
   - Authentication: API Key
   - Headers:
     - `Authorization`: `Api-Key {{ $env.YANDEX_GPT_API_KEY }}`
   - Body (JSON):
     ```json
     {
       "modelUri": "gpt://{{ $env.YANDEX_FOLDER_ID }}/yandexgpt/latest",
       "completionOptions": {
         "temperature": 0.7,
         "maxTokens": 500
       },
       "messages": [
         {
           "role": "user",
           "text": "Создай высокочастотный запрос для Яндекса на тему: {{ $json.Заголовок }}"
         }
       ]
     }
     ```

5. **Добавить HTTP Request Node (Ollama - локальный DeepSeek):**
   - Node: `HTTP Request`
   - Method: POST
   - URL: `http://localhost:11434/api/chat`
   - Body (JSON):
     ```json
     {
       "model": "deepseek-r1:7b",
       "messages": [
         {
           "role": "system",
           "content": "Ты — SEO-копирайтер для медицинского центра на Крайнем Севере."
         },
         {
           "role": "user",
           "content": "Напиши SEO-статью на тему: {{ $json.Заголовок }}. Объем: 1500-3000 символов."
         }
       ],
       "stream": false
     }
     ```

6. **Добавить Function Node (обработка данных):**
   - Node: `Function`
   - JavaScript Code:
     ```javascript
     const yandexResponse = $node["YandexGPT"].json;
     const ollamaResponse = $node["Ollama DeepSeek"].json;
     
     const highFreqQuery = yandexResponse.result.alternatives[0].message.text;
     const articleText = ollamaResponse.message.content;
     
     return {
       json: {
         query: highFreqQuery,
         article: articleText,
         topicId: $json.ID
       }
     };
     ```

7. **Добавить Google Sheets Node (запись результата):**
   - Node: `Google Sheets`
   - Operation: Append Row
   - Sheet Name: `Сгенерированный контент`
   - Columns:
     - `ID темы`: `{{ $json.topicId }}`
     - `Текст`: `{{ $json.article }}`
     - `Запрос`: `{{ $json.query }}`

8. **Добавить WordPress Node (публикация):**
   - Node: `WordPress`
   - Operation: Create Post
   - URL: `https://entuziastov75.ru/wp-json`
   - Credentials: Username + Application Password
   - Title: `{{ $json.query }}`
   - Content: `{{ $json.article }}`
   - Status: `publish`

9. **Соединить узлы стрелками**

10. **Активировать workflow**

---

### Конфигурация n8n для интеграции с локальными сервисами

**Создать `.env` файл для n8n:**

```env
# n8n/.env

# n8n настройки
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure_password_123
N8N_HOST=localhost
N8N_PORT=5678

# Локальные сервисы
OLLAMA_API_URL=http://host.docker.internal:11434/api/chat
STABLE_DIFFUSION_API_URL=http://host.docker.internal:7860

# Облачные API
YANDEX_GPT_API_KEY=AQVNxxxxxxxxxx
YANDEX_FOLDER_ID=b1gxxxxxxxxxx
GOOGLE_SHEET_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ...

# WordPress
WORDPRESS_URL=https://entuziastov75.ru
WORDPRESS_USER=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Примечание:** `host.docker.internal` — специальный DNS-адрес для доступа из Docker-контейнера n8n к локальным сервисам на Windows.

---

### Сравнение Make.com и n8n

| Критерий | Make.com | n8n |
|----------|----------|-----|
| **Стоимость** | $16-29/мес | Бесплатно (self-hosted) |
| **Лимиты** | 10,000 операций/мес (Pro) | Без лимитов |
| **Хостинг** | Только облако | Self-hosted или облако |
| **Интеграции** | 1500+ | 400+ (расширяется) |
| **Сложность** | Низкая (GUI) | Средняя (GUI + нужен сервер) |
| **Приватность** | Данные в облаке | 100% контроль |
| **Кастомизация** | Ограничена | Полная (JS-код в узлах) |
| **Рекомендация** | Для быстрого старта | Для продакшена и экономии |

---

## ЛОКАЛЬНАЯ ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ

### Установка Stable Diffusion WebUI (AUTOMATIC1111)

**Требования:**
- NVIDIA GPU с 6GB+ VRAM (минимум GTX 1660)
- Python 3.10.x
- Git

---

#### Шаг 1: Установить Python 3.10.6

https://www.python.org/downloads/release/python-3106/

**Важно:** Отметить "Add Python to PATH" при установке.

---

#### Шаг 2: Установить Git

https://git-scm.com/download/win

---

#### Шаг 3: Клонировать репозиторий Stable Diffusion WebUI

```bash
# Открыть PowerShell в папке проекта:
cd C:\Projects\content-factory-entusiast

# Клонировать:
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
```

---

#### Шаг 4: Скачать модель Stable Diffusion

**Рекомендуемая модель:** Realistic Vision v5.1 (фотореалистичные изображения)

1. Перейти на HuggingFace или Civitai:
   - https://civitai.com/models/4201/realistic-vision-v51
   
2. Скачать файл `realisticVisionV51_v51VAE.safetensors` (~2-5 GB)

3. Поместить в папку:
   ```
   stable-diffusion-webui/models/Stable-diffusion/
   ```

---

#### Шаг 5: Запустить WebUI

```bash
# В папке stable-diffusion-webui:
.\webui.bat --api --xformers

# Параметры:
# --api: включить REST API на порту 7860
# --xformers: оптимизация для NVIDIA GPU (быстрее)
```

**Первый запуск займет 5-10 минут (установка зависимостей).**

**Открыть в браузере:**
```
http://localhost:7860
```

---

#### Шаг 6: Тест генерации изображения

**Через GUI:**
1. Открыть `http://localhost:7860`
2. Вкладка `txt2img`
3. Промпт:
   ```
   Professional massage room in modern wellness center, cozy atmosphere, wooden interior, warm lighting, photorealistic style, high quality, 4K
   ```
4. Negative Prompt:
   ```
   blurry, low quality, distorted, text, watermark, cartoon, anime
   ```
5. Settings:
   - Width: 1080
   - Height: 1080
   - Steps: 30
   - CFG Scale: 7
   - Sampler: DPM++ 2M Karras
6. Нажать `Generate`

**Через API (Python):**

```python
# scripts/sd_image_generator.py
import requests
import base64
import os

SD_API_URL = os.getenv('STABLE_DIFFUSION_API_URL', 'http://127.0.0.1:7860')

def generate_image_sd(prompt, negative_prompt='', width=1080, height=1080):
    """
    Генерация изображения через Stable Diffusion WebUI API.
    """
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": 30,
        "sampler_name": "DPM++ 2M Karras",
        "cfg_scale": 7,
        "seed": -1
    }
    
    response = requests.post(f'{SD_API_URL}/sdapi/v1/txt2img', json=payload, timeout=300)
    
    if response.status_code == 200:
        r = response.json()
        image_data = base64.b64decode(r['images'][0])
        
        output_path = f'data/generated/images/sd_{hash(prompt)}.png'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f'✅ Image generated: {output_path}')
        return output_path
    else:
        raise Exception(f'SD API error: {response.status_code} - {response.text}')

# Пример:
if __name__ == '__main__':
    prompt = "Professional massage therapist working with client, modern spa interior, warm lighting, photorealistic, 4K"
    negative = "blurry, low quality, distorted, text"
    
    generate_image_sd(prompt, negative, width=1080, height=1080)
```

```bash
python scripts/sd_image_generator.py
```

---

### Интеграция Stable Diffusion с n8n

**Создать Flask-сервер для webhook:**

```python
# scripts/sd_api_server.py
from flask import Flask, request, jsonify
import sd_image_generator

app = Flask(__name__)

@app.route('/generate_image', methods=['POST'])
def generate_image_endpoint():
    """
    Endpoint для n8n: генерация изображения через SD.
    """
    data = request.json
    prompt = data.get('prompt')
    negative_prompt = data.get('negative_prompt', 'blurry, low quality')
    width = data.get('width', 1080)
    height = data.get('height', 1080)
    
    try:
        image_path = sd_image_generator.generate_image_sd(
            prompt, negative_prompt, width, height
        )
        
        # Вернуть публичный URL (нужно настроить веб-сервер или использовать ngrok)
        public_url = f'http://localhost:8000/{image_path}'
        
        return jsonify({
            'success': True,
            'image_url': public_url,
            'local_path': image_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
```

```bash
# Запустить сервер:
python scripts/sd_api_server.py

# В другом терминале запустить ngrok для публичного URL:
ngrok http 5001
```

**В n8n workflow:**

1. Добавить `HTTP Request` Node:
   - Method: POST
   - URL: `https://your-ngrok-url.ngrok.io/generate_image`
   - Body (JSON):
     ```json
     {
       "prompt": "{{ $json.image_prompt }}",
       "negative_prompt": "blurry, low quality",
       "width": 1080,
       "height": 1080
     }
     ```

2. Результат: `{{ $json.image_url }}`

---

### Альтернатива: Kandinsky 3.1 (Российская модель от Sber)

**API:** https://fusionbrain.ai/

**Преимущества:**
- Российская разработка (Sber AI)
- Бесплатный доступ (с лимитами)
- Хорошее качество изображений

**Минусы:**
- Облачный API (нет локальной установки)
- Лимиты на количество запросов

**Интеграция аналогична YandexGPT (HTTP Request Node).**

---

## АДАПТАЦИЯ АРХИТЕКТУРЫ ПРОЕКТА

### Новая архитектура с локальными сервисами

```
┌─────────────────────────────────────────────────────────────┐
│                    КОНТЕНТ-ЗАВОД (ЛОКАЛЬНЫЙ)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  1. ХРАНИЛИЩЕ ДАННЫХ (без изменений)                       │
├─────────────────────────────────────────────────────────────┤
│  Google Sheets (5 листов)                                  │
│  └─ Синхронизация через scripts/data_sync.py               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2. ОРКЕСТРАТОР WORKFLOW                                    │
├─────────────────────────────────────────────────────────────┤
│  БЫЛО: Make.com (облако, $16/мес)                          │
│  СТАЛО: n8n (Docker на Windows, бесплатно)                 │
│  └─ URL: http://localhost:5678                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  3. LLM ДВИЖКИ (гибрид)                                     │
├─────────────────────────────────────────────────────────────┤
│  70% запросов: DeepSeek R1 (Ollama, локально)              │
│  └─ URL: http://localhost:11434/api/chat                    │
│                                                             │
│  30% запросов: YandexGPT 4 (облако РФ, $10/мес)            │
│  └─ URL: https://llm.api.cloud.yandex.net/...               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  4. ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ                                   │
├─────────────────────────────────────────────────────────────┤
│  БЫЛО: DALL-E / Midjourney (облако, $30/мес)               │
│  СТАЛО: Stable Diffusion XL (локально, бесплатно)          │
│  └─ URL: http://localhost:7860/sdapi/v1/txt2img             │
│                                                             │
│  Альтернатива: Kandinsky 3.1 (облако РФ, бесплатно)        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  5. ГЕНЕРАЦИЯ ВИДЕО (без изменений или минимальные)        │
├─────────────────────────────────────────────────────────────┤
│  Kling AI (облако, $15/мес)                                │
│  └─ Пока нет полноценной локальной замены                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  6. ОБРАБОТКА МЕДИА (локально)                              │
├─────────────────────────────────────────────────────────────┤
│  FFmpeg (нативно на Windows)                               │
│  └─ Добавление логотипа, субтитров, конвертация            │
│                                                             │
│  Whisper (Faster Whisper, локально)                        │
│  └─ Генерация субтитров для видео                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  7. ЛОКАЛЬНЫЕ СКРИПТЫ (расширенные)                         │
├─────────────────────────────────────────────────────────────┤
│  scripts/data_sync.py       - Синхронизация Google Sheets  │
│  scripts/content_generator.py - Генерация текста (Ollama)  │
│  scripts/sd_image_generator.py - Генерация изображений (SD)│
│  scripts/video_processor.py - Обработка видео (FFmpeg)     │
│  scripts/subtitle_generator.py - Субтитры (Whisper)        │
│  scripts/sd_api_server.py   - Flask-сервер для n8n         │
│  scripts/backup.py          - Резервное копирование         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  8. ПУБЛИКАЦИЯ (без изменений)                              │
├─────────────────────────────────────────────────────────────┤
│  10+ платформ через API:                                    │
│  YouTube, VK, Telegram, Instagram, Pinterest, TikTok,       │
│  Дзен, WordPress, Одноклассники, RuTube                     │
└─────────────────────────────────────────────────────────────┘
```

---

### Обновленная структура проекта

```
content-factory-entusiast/
│
├── .env                        # API-ключи (локальные и облачные)
├── .gitignore                  # Исключить .env, data/generated/
│
├── config/
│   ├── platforms.json          # Конфигурация платформ
│   ├── prompts.json            # Промпты для AI
│   ├── tone_of_voice.md        # Tone of voice документ
│   └── services_endpoints.json # URL всех сервисов
│
├── data/
│   ├── услуги.csv              # Экспорт из Google Sheets
│   ├── темы_контента.csv
│   ├── generated/
│   │   ├── texts/
│   │   ├── images/
│   │   └── videos/
│   └── cache/                  # Кэш результатов (экономия API)
│
├── scripts/
│   ├── data_sync.py            # Синхронизация Google Sheets
│   ├── content_generator.py   # Генерация текста (Ollama/YandexGPT)
│   ├── sd_image_generator.py  # Stable Diffusion генерация
│   ├── sd_api_server.py        # Flask-сервер для n8n
│   ├── video_processor.py     # FFmpeg обработка видео
│   ├── subtitle_generator.py  # Whisper субтитры
│   ├── publisher.py            # Публикация на платформы
│   └── backup.py               # Резервное копирование
│
├── n8n/
│   ├── docker-compose.yml      # n8n конфигурация
│   ├── workflows/
│   │   ├── 1_seo_articles.json
│   │   ├── 2_social_posts.json
│   │   ├── 3_video_content.json
│   │   └── README.md
│   └── credentials.json        # n8n credentials (не коммитить)
│
├── stable-diffusion-webui/    # Клонированный репозиторий SD
│   └── models/
│       └── Stable-diffusion/
│           └── realisticVisionV51_v51VAE.safetensors
│
├── assets/
│   ├── logo.png                # Логотип Центра "Энтузиаст"
│   ├── brand_colors.json       # Цвета бренда
│   └── fonts/
│
└── docs/
    ├── SETUP_GUIDE.md          # Этот файл
    ├── API_LIMITS.md           # Лимиты API
    ├── TROUBLESHOOTING.md      # Решение проблем
    └── CHANGELOG.md            # История изменений
```

---

## ИЗМЕНЕНИЯ В WORKFLOW

### Workflow #1: SEO-статьи (адаптированный)

**Было (Make.com + OpenAI):**
```
[Schedule] → [Google Sheets] → [YandexGPT] → [OpenAI GPT-4] → [DALL-E] → [Google Sheets] → [WordPress]
```

**Стало (n8n + Ollama + Stable Diffusion):**
```
[Cron] → [Google Sheets] → [YandexGPT] → [Ollama DeepSeek] → [SD WebUI] → [Google Sheets] → [WordPress]
```

**Изменения:**
1. **Триггер:** `Schedule` → `Cron` (аналог)
2. **LLM:** `OpenAI GPT-4` → `Ollama DeepSeek R1:7b` (http://localhost:11434)
3. **Изображения:** `DALL-E` → `Stable Diffusion WebUI` (http://localhost:7860)
4. **Оркестратор:** `Make.com` → `n8n` (http://localhost:5678)

**Ключевые URL для замены:**

| Компонент | Было | Стало |
|-----------|------|-------|
| LLM API | `https://api.openai.com/v1/chat/completions` | `http://localhost:11434/api/chat` |
| Image API | `https://api.openai.com/v1/images/generations` | `http://localhost:7860/sdapi/v1/txt2img` |
| Оркестратор | `https://www.make.com/` | `http://localhost:5678` |

---

### Пример n8n workflow (JSON экспорт)

```json
{
  "name": "SEO Articles Generation (Local)",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "days",
              "daysInterval": 2
            }
          ]
        }
      },
      "name": "Every 2 days at 10:00",
      "type": "n8n-nodes-base.cron",
      "position": [250, 300]
    },
    {
      "parameters": {
        "operation": "getRows",
        "sheetId": "Темы контента",
        "filters": {
          "fields": [
            {
              "column": "Статус",
              "value": "черновик"
            }
          ]
        },
        "limit": 1
      },
      "name": "Get Topic from Google Sheets",
      "type": "n8n-nodes-base.googleSheets",
      "position": [450, 300]
    },
    {
      "parameters": {
        "url": "http://localhost:11434/api/chat",
        "method": "POST",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={\n  \"model\": \"deepseek-r1:7b\",\n  \"messages\": [\n    {\n      \"role\": \"system\",\n      \"content\": \"Ты — SEO-копирайтер для медицинского центра на Крайнем Севере.\"\n    },\n    {\n      \"role\": \"user\",\n      \"content\": \"Напиши SEO-статью на тему: {{ $json.Заголовок }}. Объем: 1500-3000 символов.\"\n    }\n  ],\n  \"stream\": false\n}"
      },
      "name": "Generate Article (Ollama DeepSeek)",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "http://localhost:7860/sdapi/v1/txt2img",
        "method": "POST",
        "jsonParameters": true,
        "bodyParametersJson": "={\n  \"prompt\": \"Professional {{ $json['Название услуги'] }} in modern wellness center, photorealistic, 4K\",\n  \"negative_prompt\": \"blurry, low quality, text\",\n  \"width\": 1200,\n  \"height\": 630,\n  \"steps\": 30\n}"
      },
      "name": "Generate Image (Stable Diffusion)",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    },
    {
      "parameters": {
        "operation": "create",
        "title": "={{ $json.Заголовок }}",
        "content": "={{ $node['Generate Article (Ollama DeepSeek)'].json.message.content }}",
        "status": "publish"
      },
      "name": "Publish to WordPress",
      "type": "n8n-nodes-base.wordpress",
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Every 2 days at 10:00": {
      "main": [[{"node": "Get Topic from Google Sheets", "type": "main", "index": 0}]]
    },
    "Get Topic from Google Sheets": {
      "main": [[{"node": "Generate Article (Ollama DeepSeek)", "type": "main", "index": 0}]]
    },
    "Generate Article (Ollama DeepSeek)": {
      "main": [[{"node": "Generate Image (Stable Diffusion)", "type": "main", "index": 0}]]
    },
    "Generate Image (Stable Diffusion)": {
      "main": [[{"node": "Publish to WordPress", "type": "main", "index": 0}]]
    }
  }
}
```

**Импорт в n8n:**
1. Сохранить JSON как `workflow_1_local.json`
2. Открыть n8n → Import from File → Выбрать файл
3. Настроить credentials (Google Sheets, WordPress)
4. Активировать

---

## КОНФИГУРАЦИОННЫЕ ФАЙЛЫ

### config/services_endpoints.json

```json
{
  "llm": {
    "primary": {
      "name": "Ollama DeepSeek",
      "url": "http://localhost:11434/api/chat",
      "model": "deepseek-r1:7b",
      "type": "local",
      "cost_per_1k_tokens": 0
    },
    "secondary": {
      "name": "YandexGPT 4",
      "url": "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
      "model": "yandexgpt/latest",
      "type": "cloud",
      "cost_per_1k_tokens": 0.01
    }
  },
  "image_generation": {
    "primary": {
      "name": "Stable Diffusion XL",
      "url": "http://localhost:7860/sdapi/v1/txt2img",
      "type": "local",
      "cost_per_image": 0
    },
    "secondary": {
      "name": "Kandinsky 3.1",
      "url": "https://api-key.fusionbrain.ai/",
      "type": "cloud",
      "cost_per_image": 0
    }
  },
  "video_generation": {
    "primary": {
      "name": "Kling AI",
      "url": "https://api.klingai.com/v1/videos/generations",
      "type": "cloud",
      "cost_per_video": 0.5
    }
  },
  "orchestration": {
    "name": "n8n",
    "url": "http://localhost:5678",
    "type": "local",
    "cost_per_month": 0
  },
  "data_storage": {
    "name": "Google Sheets",
    "spreadsheet_id": "YOUR_SPREADSHEET_ID_HERE",
    "type": "cloud",
    "cost_per_month": 0
  }
}
```

---

### config/prompts.json

```json
{
  "seo_article": {
    "system": "Ты — SEO-копирайтер для Центра здоровья 'Энтузиаст' на Крайнем Севере (Ноябрьск, ЯНАО). Твой стиль: дружелюбный, экспертный, заботливый. Учитывай специфику региона: полярная ночь, суровый климат, вахтовый метод работы.",
    "user_template": "Напиши SEO-оптимизированную статью на тему: '{topic}'.\n\nДанные об услуге:\n- Название: {service_name}\n- Описание: {service_description}\n- Показания: {service_indications}\n- Цена: {service_price}\n- Длительность: {service_duration}\n\nТребования:\n- Объем: 1500-3000 символов\n- Структура: введение, 3-4 подраздела с H2-заголовками, заключение с призывом к действию\n- Упоминай боли ЦА: усталость, недостаток солнца, стресс от суровых условий\n- Формат: чистый HTML с тегами <h2>, <p>, <ul>/<li>"
  },
  "social_post": {
    "system": "Ты — SMM-менеджер для Центра здоровья 'Энтузиаст'. Стиль: дружелюбный, эмоциональный, использование эмодзи. Обращение на 'Вы'.",
    "user_template": "Создай привлекательный пост для социальных сетей на тему: '{topic}'.\n\nДанные об услуге:\n- Название: {service_name}\n- Краткое описание: {service_short_description}\n- Цена: {service_price}\n\nТребования:\n- Объем: 150-300 символов\n- Включи призыв к действию\n- Используй 2-3 эмодзи\n- Формат: обычный текст без HTML"
  },
  "video_prompt": {
    "system": "Ты — режиссер рекламных видео для медицинского центра.",
    "user_template": "Создай детальный технический промпт для AI-генератора видео (Kling/Sora) на тему: '{topic}'.\n\nТребования к промпту:\n- Формат: вертикальный 9:16 (iPhone)\n- Длительность: 30-60 секунд\n- Стиль: UGC-like (как снято клиентом на смартфон)\n- Освещение: естественное, теплое (5200K)\n- Локация: современный медицинский центр, северный интерьер\n- Сцены: опиши 3-4 ключевых момента с таймингом\n- Формат вывода: английский промпт, не более 500 слов"
  },
  "image_prompt": {
    "template": "Professional {service_name} in modern wellness center, cozy atmosphere, northern interior design, warm lighting, photorealistic style, high quality, 4K, {aspect_ratio}"
  },
  "image_negative_prompt": {
    "default": "blurry, low quality, distorted, text, watermark, cartoon, anime, ugly, deformed"
  }
}
```

---

## РАЗВЕРТЫВАНИЕ НА WINDOWS 10

### Полная последовательность установки

#### Шаг 1: Подготовка системы

```powershell
# 1. Обновить Windows 10 до последней версии
# Settings → Update & Security → Check for updates

# 2. Включить WSL2 (для Docker)
wsl --install
# Перезагрузить компьютер

# 3. Установить Docker Desktop
# Скачать: https://www.docker.com/products/docker-desktop/
# Запустить установщик, отметить "Use WSL 2"
```

---

#### Шаг 2: Установка Python и зависимостей

```powershell
# 1. Установить Python 3.10.6
# https://www.python.org/downloads/release/python-3106/
# Отметить "Add Python to PATH"

# 2. Проверить установку:
python --version
# Должно быть: Python 3.10.6

# 3. Установить pip-зависимости:
pip install openai requests pandas python-dotenv google-api-python-client Pillow flask faster-whisper
```

---

#### Шаг 3: Установка Ollama (DeepSeek)

```powershell
# 1. Скачать установщик Ollama:
# https://ollama.com/download/windows

# 2. Запустить OllamaSetup.exe

# 3. Открыть PowerShell и скачать модель:
ollama pull deepseek-r1:7b

# 4. Проверить:
ollama list
# Должно быть: deepseek-r1:7b

# 5. Запустить (автоматически в фоне):
# Ollama работает на http://localhost:11434
```

---

#### Шаг 4: Установка Stable Diffusion WebUI

```powershell
# 1. Установить Git:
# https://git-scm.com/download/win

# 2. Клонировать репозиторий:
cd C:\Projects
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# 3. Скачать модель Realistic Vision v5.1:
# https://civitai.com/models/4201/realistic-vision-v51
# Сохранить realisticVisionV51_v51VAE.safetensors в:
# models\Stable-diffusion\

# 4. Запустить WebUI:
.\webui.bat --api --xformers

# Первый запуск займет 5-10 минут
# После завершения открыть: http://localhost:7860
```

---

#### Шаг 5: Установка n8n (Docker)

```powershell
# 1. Создать папку проекта:
mkdir C:\Projects\content-factory-entusiast\n8n
cd C:\Projects\content-factory-entusiast\n8n

# 2. Создать docker-compose.yml (скопировать из секции выше)

# 3. Запустить n8n:
docker-compose up -d

# 4. Проверить статус:
docker ps
# Должен быть контейнер n8n

# 5. Открыть n8n:
# http://localhost:5678
# Логин: admin / Пароль: (из docker-compose.yml)
```

---

#### Шаг 6: Настройка проекта

```powershell
# 1. Клонировать структуру проекта:
cd C:\Projects
git clone <your-repo-url> content-factory-entusiast
cd content-factory-entusiast

# 2. Создать .env файл:
# Скопировать .env.example → .env
# Заполнить API-ключи

# 3. Синхронизировать Google Sheets:
python scripts/data_sync.py

# 4. Запустить Flask-сервер для n8n:
python scripts/sd_api_server.py
# В другом терминале:
ngrok http 5001
# Скопировать URL для n8n

# 5. Импортировать workflow в n8n:
# Открыть http://localhost:5678
# Import from File → n8n/workflows/1_seo_articles.json
# Настроить credentials
```

---

#### Шаг 7: Автоматизация запуска

**Создать bat-файлы для автозапуска:**

**start_all_services.bat:**
```batch
@echo off
echo Starting Content Factory Services...

echo [1/4] Starting Ollama...
REM Ollama запускается автоматически при установке

echo [2/4] Starting Stable Diffusion WebUI...
start /B cmd /c "cd C:\Projects\stable-diffusion-webui && webui.bat --api --xformers"

echo [3/4] Starting n8n...
start /B cmd /c "cd C:\Projects\content-factory-entusiast\n8n && docker-compose up"

echo [4/4] Starting Flask API Server...
start /B cmd /c "cd C:\Projects\content-factory-entusiast && python scripts/sd_api_server.py"

echo.
echo All services started!
echo.
echo URLs:
echo - Ollama: http://localhost:11434
echo - Stable Diffusion: http://localhost:7860
echo - n8n: http://localhost:5678
echo - Flask API: http://localhost:5001
echo.
pause
```

**Добавить в автозагрузку Windows:**
1. Нажать `Win + R`
2. Ввести: `shell:startup`
3. Создать ярлык для `start_all_services.bat`

---

## TROUBLESHOOTING

### Проблема 1: Ollama не запускается

**Симптомы:**
```
Error: connection refused at http://localhost:11434
```

**Решение:**
```powershell
# 1. Проверить, запущен ли Ollama:
tasklist | findstr ollama

# 2. Если нет, запустить вручную:
ollama serve

# 3. Проверить порт:
netstat -an | findstr 11434
```

---

### Проблема 2: Stable Diffusion выдает ошибку CUDA

**Симптомы:**
```
RuntimeError: CUDA out of memory
```

**Решение:**
```powershell
# 1. Уменьшить разрешение изображения:
# width: 1080 → 768
# height: 1080 → 768

# 2. Уменьшить количество steps:
# steps: 30 → 20

# 3. Добавить параметр --medvram при запуске:
.\webui.bat --api --xformers --medvram

# Для очень слабых GPU (4-6GB VRAM):
.\webui.bat --api --xformers --lowvram
```

---

### Проблема 3: n8n не видит localhost-сервисы

**Симптомы:**
```
Error: connect ECONNREFUSED 127.0.0.1:11434
```

**Решение:**
```powershell
# Docker на Windows не видит localhost хоста
# Использовать специальный DNS:

# Вместо:
http://localhost:11434

# Использовать:
http://host.docker.internal:11434

# Обновить все URL в n8n workflow:
# - Ollama: http://host.docker.internal:11434
# - Stable Diffusion: http://host.docker.internal:7860
# - Flask API: http://host.docker.internal:5001
```

---

### Проблема 4: DeepSeek генерирует медленно

**Симптомы:**
```
Генерация текста занимает 5-10 минут
```

**Решение:**
```powershell
# 1. Проверить, используется ли GPU:
ollama ps
# Должно быть: GPU

# 2. Если GPU не используется, переустановить драйверы NVIDIA:
# https://www.nvidia.com/Download/index.aspx

# 3. Использовать меньшую модель:
ollama pull deepseek-r1:1.5b
# Быстрее, но ниже качество

# 4. Для критичных задач использовать YandexGPT (облако):
# Быстрее локального DeepSeek
```

---

### Проблема 5: Google Sheets API превышает лимиты

**Симптомы:**
```
Error 429: Too Many Requests
```

**Решение:**
```python
# 1. Добавить rate limiting в scripts/data_sync.py:

import time

def sync_with_rate_limit():
    for sheet_name, range_name in sheets_config.items():
        print(f'Syncing {sheet_name}...')
        df = get_google_sheet_data(sheet_name, range_name)
        df.to_csv(f'data/{sheet_name}.csv', index=False)
        
        # Пауза 2 секунды между запросами
        time.sleep(2)

# 2. Использовать кэширование:
# Не синхронизировать Google Sheets каждый раз,
# а только раз в час/день
```

---

## ЗАКЛЮЧЕНИЕ

### Итоги локализации

**Достигнуто:**
- ✅ Снижение затрат с $146/мес до $25/мес (-83%)
- ✅ Полный контроль над генерацией контента
- ✅ Независимость от зарубежных сервисов
- ✅ Приватность данных (локальная обработка)
- ✅ Гибкость настройки под специфику проекта

**Компромиссы:**
- ⚠️ Требуется мощное железо (GPU 12GB+, 16GB RAM)
- ⚠️ Более сложная настройка (Docker, WSL, API-серверы)
- ⚠️ Нет полноценной замены для генерации видео (Sora/Kling)
- ⚠️ Локальные модели могут быть медленнее облачных

**Рекомендуемая конфигурация:**

| Компонент | Решение | Причина |
|-----------|---------|---------|
| **Оркестратор** | n8n (Docker) | Бесплатно, полный контроль |
| **LLM (70%)** | Ollama DeepSeek | Бесплатно, приватность |
| **LLM (30%)** | YandexGPT | Скорость, качество |
| **Изображения** | Stable Diffusion | Бесплатно, хорошее качество |
| **Видео** | Kling AI (облако) | Нет локальных аналогов |
| **Обработка медиа** | FFmpeg + Whisper | Открытые, надежные |

---

### Следующие шаги

1. **Развернуть локальное окружение по этому гайду**
2. **Протестировать каждый компонент отдельно**
3. **Импортировать workflow в n8n**
4. **Запустить первый цикл генерации контента**
5. **Оптимизировать промпты и параметры**
6. **Масштабировать до 100+ публикаций в день**

---

### Полезные ссылки

**Документация:**
- Ollama: https://github.com/ollama/ollama
- n8n: https://docs.n8n.io/
- Stable Diffusion WebUI: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- YandexGPT: https://cloud.yandex.ru/docs/yandexgpt/
- Faster Whisper: https://github.com/guillaumekln/faster-whisper

**Сообщества:**
- n8n Community: https://community.n8n.io/
- Stable Diffusion Reddit: https://www.reddit.com/r/StableDiffusion/
- Ollama Discord: https://discord.gg/ollama

---

**ГАЙД ГОТОВ К ИСПОЛЬЗОВАНИЮ. УСПЕШНОЙ ЛОКАЛИЗАЦИИ КОНТЕНТ-ЗАВОДА!**
