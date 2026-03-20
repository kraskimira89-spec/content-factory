# CUDA 12 + GPU для rembg (Windows)

Пошаговая установка для ускорения **rembg** / **ONNX Runtime** на видеокарте NVIDIA.  
**Ollama** ставится отдельно и обычно сама подхватывает GPU после драйвера — этот гайд в первую очередь про **Python + onnxruntime-gpu + cublasLt64_12.dll**.

---

## Перед началом

- Видеокарта **NVIDIA** с поддержкой CUDA.
- **~4–6 ГБ** свободного места на диске (Toolkit + cuDNN при необходимости).
- Права администратора для установщиков.

---

## Шаг 1. Драйвер NVIDIA

1. Откройте [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx) или **GeForce Experience** / **NVIDIA App**.
2. Установите **актуальный Game Ready или Studio** драйвер.
3. Перезагрузите ПК при запросе.

Проверка:

```powershell
nvidia-smi
```

Должна открыться таблица с версией драйвера и GPU. Если команда не найдена — драйвер не в PATH (редко); переустановите драйвер.

---

## Шаг 2. CUDA Toolkit 12.x

1. Зайдите на [CUDA Toolkit Download](https://developer.nvidia.com/cuda-downloads).
2. Выберите: **Windows** → ваша версия Windows → **exe (local)** или **network**.
3. Запустите установщик от имени администратора.
4. Оставьте компоненты по умолчанию (в т.ч. **CUDA Runtime** и библиотеки вроде **cuBLAS**).
5. Дождитесь окончания и при необходимости **перезагрузите ПК**.

Проверка (новое окно PowerShell после перезагрузки):

```powershell
nvcc --version
```

Если `nvcc` не найден — добавьте в PATH (типично):

`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin`

(замените `v12.x` на вашу папку, например `v12.6`).

---

## Шаг 3. Версия onnxruntime-gpu под вашу CUDA

Смотрите таблицу совместимости: [onnxruntime releases](https://github.com/microsoft/onnxruntime/releases) → раздел **CUDA / cuDNN**.

Для **CUDA 12.x** обычно подходит последний **onnxruntime-gpu** из PyPI (pip сам подтянет сборку под CUDA 12).

В виртуальном окружении проекта:

```powershell
cd D:\content-factory
.\venv\Scripts\activate
# или используйте тот же Python, где стоит rembg
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime-gpu
```

Если pip предложит конкретную версию — при конфликте зафиксируйте ту, что указана в документации ONNX Runtime для CUDA 12, например:

```powershell
pip install onnxruntime-gpu==1.19.2
```

(номер версии уточните по ссылке выше на момент установки.)

---

## Шаг 4. Проверка Python / GPU

```powershell
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

Ожидается в списке **`CUDAExecutionProvider`** (и часто `CPUExecutionProvider`).

Если только `CPUExecutionProvider` — CUDA DLL всё ещё не видны: проверьте PATH, перезагрузку, совпадение версии `onnxruntime-gpu` и Toolkit.

---

## Шаг 5. rembg

Пакет **rembg** использует установленный **onnxruntime**. Достаточно:

```powershell
pip install "rembg>=2.0.0"
```

Отдельно **`rembg[gpu]`** не обязателен, если уже стоит **onnxruntime-gpu** (лишние зависимости могут конфликтовать — держите одну сборку ORT).

Прогон теста:

```powershell
cd D:\content-factory\Karusel
python tests\test_agents_2_3.py
```

---

## Шаг 6. Ollama и GPU

После установки **Ollama** на Windows она обычно использует GPU **сама**, если драйвер NVIDIA в порядке. Отдельно CUDA Toolkit для Ollama не обязателен, но **не мешает**.

Проверка: в трее Ollama → при запуске модели нагрузка на GPU в **Диспетчере задач** → GPU.

---

## Частые проблемы

| Симптом | Что сделать |
|--------|-------------|
| `cublasLt64_12.dll` missing | Установлен **CUDA Toolkit 12**, не только драйвер; перезагрузка; PATH к `CUDA\v12.x\bin`. |
| Только CPU в ORT | `pip uninstall onnxruntime onnxruntime-gpu` → один раз `pip install onnxruntime-gpu`. |
| Две версии CUDA | См. блок **PATH при CUDA 12.x и 13.x** ниже или оставьте одну актуальную 12.x. |

---

## PATH при CUDA 12.x и 13.x (onnxruntime-gpu)

**onnxruntime-gpu** для CUDA 12 ищет DLL вроде `cublasLt64_12.dll`. Если в **User PATH** раньше стоит `...\CUDA\v13.x\bin`, загрузка `onnxruntime_providers_cuda.dll` может дать **ошибку 126** — при этом в Python список провайдеров всё равно может содержать `CUDAExecutionProvider`.

Скрипт **`D:\content-factory\scripts\cuda-path-auto.ps1`**:

- по умолчанию выбирает **последнюю установленную CUDA 12.x** (`-PreferCuda12 $true`);
- удаляет из User PATH старые записи `...\CUDA\v*\bin` и `...\CUDA\v*\libnvvp`;
- добавляет в **начало** `bin` и `libnvvp` выбранного корня, задаёт `CUDA_PATH`.

```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1" -Scope User
```

После запуска **закройте и откройте терминал** (или Cursor), затем: `where.exe nvcc`, `nvcc --version` — должна быть **12.x**.

Ежедневная задача Планировщика: `-RegisterTask` (в скрипте передаётся `-PreferCuda12:$true`, чтобы не откатывать PATH на v13).

---

## Краткий чеклист

1. `nvidia-smi` — OK  
2. Установлен **CUDA Toolkit 12.x**, `nvcc --version` — OK  
3. `pip install onnxruntime-gpu`, провайдеры — есть **CUDA**  
4. `rembg` / тест Karusel — без ошибки про CUDA DLL  

После этого можно считать **GPU для rembg** настроенным.
