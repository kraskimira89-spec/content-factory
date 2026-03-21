# ComfyUI — ручной запуск workflow по API

Утилита **`run_comfy_workflow.py`**: `POST /prompt` → опрос `GET /history/{prompt_id}` → скачивание через `GET /view`.

## Подготовка

1. Запустите ComfyUI (порт по умолчанию в проекте — **8000**, см. `COMFYUI_URL` в `config/.env`).
2. Положите JSON workflow:
   - либо **`comfy_api/workflow_api.json`** (по умолчанию),
   - либо путь через **`--workflow`**.

Формат файла:

- **Вариант A** — только граф API (как `Karusel/assets/carousel/comfyui_portrait.json`): объект с ключами-нодами `"3"`, `"4"`, …
- **Вариант B** — обёртка для `/prompt`:

```json
{
  "prompt": { "3": { ... }, "4": { ... } },
  "client_id": "content-factory"
}
```

## Запуск

Из корня `content-factory`:

```powershell
pip install requests
python comfy_api\run_comfy_workflow.py
```

Свой workflow и папка вывода:

```powershell
python comfy_api\run_comfy_workflow.py --workflow D:\path\workflow_api.json --output D:\content-factory\outputs
```

Другой сервер:

```powershell
python comfy_api\run_comfy_workflow.py --server http://127.0.0.1:8188
```

(или задайте `COMFYUI_URL` в `config/.env`.)

## Параметры

| Аргумент | По умолчанию |
|----------|----------------|
| `--workflow` | `comfy_api/workflow_api.json` |
| `--output` | `outputs/` в корне репозитория |
| `--history-dir` | `history/` — сюда пишется полный JSON ответа `GET /history/{prompt_id}` в файл `{prompt_id}.json` |
| `--server` | из `COMFYUI_URL` / `shared-config` |
| `--poll-interval` | `2` сек |
| `--timeout` | `600` сек |
| `--client-id` | `content-factory` |

## Связь с Karusel

Agent 3b использует тот же протокол внутри `Karusel/agents/agent3b_chargen.py`. Этот скрипт — **отладочный/ручной** прогон без пайплайна карусели.
