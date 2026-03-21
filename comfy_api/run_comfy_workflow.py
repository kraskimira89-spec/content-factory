"""
Утилита: отправить workflow в ComfyUI (/prompt), дождаться history, сохранить history в JSON, скачать картинки (/view).

Запуск из корня репозитория:
  python comfy_api/run_comfy_workflow.py
  python comfy_api/run_comfy_workflow.py --workflow Karusel/assets/carousel/comfyui_portrait.json

Базовый URL: COMFYUI_URL в config/.env или comfyui.url_default в shared-config (по умолчанию http://127.0.0.1:8000).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.shared_config import get_comfyui_url  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ComfyUI: queue workflow, poll history, download images.")
    p.add_argument(
        "--workflow",
        type=Path,
        default=_PROJECT_ROOT / "comfy_api" / "workflow_api.json",
        help="JSON: либо обёртка {prompt, client_id}, либо только граф нод (как API export).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=_PROJECT_ROOT / "outputs",
        help="Папка для скачанных файлов.",
    )
    p.add_argument(
        "--history-dir",
        type=Path,
        default=_PROJECT_ROOT / "history",
        help="Папка для сохранения полного ответа GET /history/{prompt_id} как JSON.",
    )
    p.add_argument(
        "--server",
        default="",
        help="Переопределить базовый URL (иначе COMFYUI_URL / shared-config).",
    )
    p.add_argument("--poll-interval", type=float, default=2.0, help="Секунды между опросами history.")
    p.add_argument("--timeout", type=float, default=600.0, help="Макс. ожидание выполнения (сек).")
    p.add_argument(
        "--client-id",
        default="content-factory",
        help="client_id в теле /prompt (если в JSON его нет).",
    )
    return p.parse_args()


def _base_url(args: argparse.Namespace) -> str:
    raw = (args.server or "").strip().rstrip("/")
    if not raw:
        raw = get_comfyui_url().strip().rstrip("/")
    return raw


def queue_prompt(base: str, workflow_path: Path, client_id: str) -> str:
    data = json.loads(workflow_path.read_text(encoding="utf-8"))

    if "prompt" in data:
        payload = data
        if "client_id" not in payload:
            payload = {**payload, "client_id": client_id}
    else:
        payload = {"prompt": data, "client_id": client_id}

    url = f"{base}/prompt"
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    j = resp.json()
    print("queue_prompt response:", j)
    if "prompt_id" not in j:
        raise RuntimeError(f"В ответе /prompt нет prompt_id: {j}")
    return j["prompt_id"]


def get_history(base: str, prompt_id: str) -> dict:
    url = f"{base}/history/{prompt_id}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def save_history(history_dir: Path, prompt_id: str, history_obj: dict) -> Path:
    """Сохраняет весь объект history в history/{prompt_id}.json."""
    history_dir.mkdir(parents=True, exist_ok=True)
    path = history_dir / f"{prompt_id}.json"
    path.write_text(
        json.dumps(history_obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("History saved to:", path)
    return path


def wait_for_completion(
    base: str,
    prompt_id: str,
    poll_interval: float,
    timeout: float,
    history_dir: Path,
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = get_history(base, prompt_id)
        entry = history.get(prompt_id) or {}
        outputs = entry.get("outputs") or {}
        if outputs:
            print("Workflow finished.")
            save_history(history_dir, prompt_id, history)
            return entry
        print("Still running...", prompt_id)
        time.sleep(poll_interval)
    raise TimeoutError(f"Истёк timeout ({timeout}s), prompt_id={prompt_id}")


def download_image(base: str, filename: str, subfolder: str, folder_type: str, output_dir: Path) -> Path:
    params = {
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type,
    }
    url = f"{base}/view"
    resp = requests.get(url, params=params, timeout=120)
    resp.raise_for_status()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename
    out_path.write_bytes(resp.content)
    print("Saved:", out_path)
    return out_path


def main() -> int:
    args = _parse_args()
    workflow_path = args.workflow
    if not workflow_path.is_file():
        print(f"Файл workflow не найден: {workflow_path}", file=sys.stderr)
        print("Создайте comfy_api/workflow_api.json или укажите --workflow.", file=sys.stderr)
        return 1

    base = _base_url(args)
    print("ComfyUI base URL:", base)

    print("Queueing prompt...")
    prompt_id = queue_prompt(base, workflow_path, args.client_id)
    print("Got prompt_id:", prompt_id)

    print("Waiting for completion...")
    try:
        entry = wait_for_completion(
            base,
            prompt_id,
            args.poll_interval,
            args.timeout,
            args.history_dir,
        )
    except TimeoutError as e:
        print(e, file=sys.stderr)
        return 2

    outputs = entry.get("outputs", {})
    for _node_id, node_data in outputs.items():
        for img in node_data.get("images", []):
            filename = img["filename"]
            subfolder = img.get("subfolder", "")
            folder_type = img.get("type", "output")
            download_image(base, filename, subfolder, folder_type, args.output)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
