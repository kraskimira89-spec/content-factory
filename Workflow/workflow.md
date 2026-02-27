# workflow.md — от нуля до генерации картинок и текстов

## 0. Стартовые условия

- ПК с Windows 10.
- Видеокарта: NVIDIA RTX 3060 12 GB.
- Интернет‑доступ.
- Свободно ≥ 50 GB на диске D: (на AI‑папку).

Рабочая директория: `D:\AI`.

---

## 1. Подготовка железа (MSI Afterburner)

1. Установить MSI Afterburner (вместе с RivaTuner).
2. Вкладка «Основные»:
   - включить «Разрешить управление напряжением» (стандартное MSI),
   - включить «Разрешить мониторинг напряжения».
3. В главном окне:
   - Temp Limit: 75 °C,
   - Power Limit: 95 %.
4. Лёгкий андервольт:
   - `Ctrl+F` → кривая напряжение/частота,
   - точка 0.9 V → выставить частоту ~1900 MHz,
   - применить.
5. Лёгкий разгон памяти:
   - Memory Clock: +300 MHz,
   - сохранить в профиль 1.
6. Проверка:
   - FurMark 1920×1080, 10–15 минут,
   - температура не выше ~75–78 °C, без артефактов и вылетов.

---

## 2. Установка Python и Git

1. Удалить старые версии Python 3.11 (если есть) через «Программы и компоненты».
2. Установить Python 3.10 (x64) — инсталлятор или Microsoft Store.
3. Проверка в CMD:

   ```cmd
   where python
   python --version

cd /d D:\
mkdir AI
cd AI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

3. Установка Stable Diffusion WebUI (AUTOMATIC1111)
3.1. Клонирование репозитория
text
cd /d D:\
mkdir AI
cd AI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
Структура: D:\AI\stable-diffusion-webui.

3.2. Первый запуск и установка зависимостей
text
cd /d D:\AI\stable-diffusion-webui
webui-user.bat
Скрипт создаст venv на Python 3.10 и установит зависимости.

Важно дождаться строки:

text
Running on local URL:  http://127.0.0.1:7860
Открыть в браузере http://127.0.0.1:7860 — интерфейс SD.

4. Подключение базовой модели SD 1.5
4.1. Скачивание модели
С сайта‑инструкции или HuggingFace скачать файл:

v1-5-pruned-emaonly.safetensors (≈ 3.9–4.0 GB).

Переместить его в папку:

D:\AI\stable-diffusion-webui\models\Stable-diffusion.

4.2. Перезапуск WebUI
text
cd /d D:\AI\stable-diffusion-webui
webui-user.bat
Открыть http://127.0.0.1:7860.

4.3. Выбор чекпоинта и тест
Вверху слева выбрать в списке Stable Diffusion checkpoint:
v1-5-pruned-emaonly.safetensors.

Вкладка txt2img:

Prompt: a cute cat,

Size: 512×512,

Steps: 20.

Нажать Generate — появится тестовая картинка.

5. Оптимизация SD под RTX 3060
Остановить WebUI (закрыть окно CMD).

Открыть webui-user.bat (правый клик → Изменить).

Найти строку:

text
set COMMANDLINE_ARGS=
и заменить на:

text
set COMMANDLINE_ARGS=--medvram --opt-sdp-attention
Сохранить, снова запустить:

text
cd /d D:\AI\stable-diffusion-webui
webui-user.bat
Это уменьшит потребление VRAM и чуть ускорит работу на NVIDIA.

6. Установка и проверка Ollama (LLM)
6.1. Установка
Скачать установщик для Windows с официального сайта Ollama.

Установить (по умолчанию в C:\Users\user\AppData\Local\Programs\Ollama).

Открыть PowerShell:

powershell
ollama --version
6.2. Тест: скачивание модели и проверка GPU
Запустить модель, например:

powershell
ollama run deepseek-r1:8b
В новом окне PowerShell:

powershell
nvidia-smi
В списке процессов должен появиться ollama и использование видеопамяти.

Если GPU не используется — задать переменные для текущей сессии:

powershell
$env:CUDA_VISIBLE_DEVICES="0"
ollama run deepseek-r1:8b
7. Базовые сценарии генерации
7.1. Сценарий «Картинка из текста» (SD)
Запустить WebUI (webui-user.bat).

Выбрать модель v1-5-pruned-emaonly.

Во вкладке txt2img:

короткий Prompt: описание сцены,

нужный размер (512×512 или 768×768),

Steps 20–30.

Нажать Generate.

Сохранить результат через иконку дискеты.

7.2. Сценарий «Текст → LLM (Ollama)»
В PowerShell:

powershell
ollama run deepseek-r1:8b
Ввести задачу, например:

«Сделай продающий текст для этого изображения: …»

«Сгенерируй 5 вариантов заголовков…»

Скопировать результат в документы/планшеты задач.

8. Мини-чеклист перед боевым использованием
MSI Afterburner запущен, профиль разгона/андервольта активен.

Температура GPU под нагрузкой не превышает ~75 °C.

SD:

WebUI запускается без ошибок,

выбран корректный checkpoint,

тестовая генерация 512×512 проходит.

Ollama:

команды ollama list и ollama run ... работают,

в nvidia-smi видно загрузку GPU во время генерации.

9. Дальнейшие шаги (для развития проекта)
Добавить SDXL модель и настроить её запуск при ограничении VRAM.

Настроить автоматические пайплайны:

генерация пачки картинок по списку промптомов,

генерация текстов/описаний для каждой картинки.

Организовать отдельные каталоги для проектов:

D:\AI\projects\<название>\images,

D:\AI\projects\<название>\texts.

