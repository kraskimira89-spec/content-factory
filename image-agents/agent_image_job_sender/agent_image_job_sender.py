# image-agents/agent_image_job_sender — джобы в очередь или на локальный генератор
"""
Читает output/image_jobs/*.json, для каждой картинки создаёт джобу:
- либо запись в output/image_queue/ (файл-джоба),
- либо HTTP POST на локальный сервис (image_generator_url из конфига).
Содержимое джобы: prompt, style, aspect_ratio, safety_tags, target_path.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

# Пути
_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent

if str(PROJECT_ROOT / "seo-agents") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "seo-agents"))
from shared.logger import get_logger  # noqa: E402

logger = get_logger("image_agents.job_sender")

# Конфиг
_CONFIG_PATH = PROJECT_ROOT / "config" / "shared-config.json"
_CONFIG = json.loads(_CONFIG_PATH.read_text("utf-8")) if _CONFIG_PATH.exists() else {}
_IMG = _CONFIG.get("image_agents", {})
# Переопределение через IMAGE_GENERATOR_URL в config/.env (8000 = Flask image_generate_api.py)
if (PROJECT_ROOT / "config" / ".env").exists():
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / "config" / ".env")
GENERATOR_URL = os.getenv("IMAGE_GENERATOR_URL", "").strip() or _IMG.get("image_generator_url", "http://127.0.0.1:8000/generate")

JOBS_DIR = PROJECT_ROOT / _IMG.get("image_jobs_path", "output/image_jobs")
QUEUE_DIR = PROJECT_ROOT / _IMG.get("image_queue_path", "output/image_queue")
STORAGE_DIR = PROJECT_ROOT / _IMG.get("image_storage_path", "output/images")
GENERATOR_TIMEOUT = _IMG.get("image_generator_timeout_sec", 120)


def job_spec_to_payload(item: dict, post_id: str, job_index: int) -> dict:
    """Формирует тело джобы для генератора или для файла очереди."""
    image_id = item.get("id", f"img_{job_index}")
    ext = "png"
    # target_path: output/images/{post_id}-{image_id}.png
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    target_path = STORAGE_DIR / f"{post_id}-{image_id}.{ext}"
    return {
        "prompt": item.get("prompt", ""),
        "style": item.get("style", ""),
        "aspect_ratio": item.get("aspect_ratio", "16:9"),
        "safety_tags": item.get("safety_tags", []),
        "target_path": str(target_path),
        "post_id": post_id,
        "image_id": image_id,
        "purpose": item.get("purpose", ""),
    }


def send_job_to_http(payload: dict) -> bool:
    """Отправляет джобу на локальный генератор по HTTP."""
    try:
        r = requests.post(
            GENERATOR_URL,
            json=payload,
            timeout=GENERATOR_TIMEOUT,
        )
        if r.status_code in (200, 201, 202):
            logger.info("Джоба отправлена на генератор: %s", payload.get("image_id"))
            return True
        logger.warning("Генератор вернул %s: %s", r.status_code, r.text[:200])
        return False
    except requests.exceptions.RequestException as e:
        logger.error("Ошибка запроса к генератору: %s", e)
        return False


def send_job_to_queue(payload: dict) -> Path:
    """Кладут джобу в папку очереди (файл JSON). Генератор подхватывает сам."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    name = f"{payload['post_id']}_{payload['image_id']}_{ts}.json"
    path = QUEUE_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("Джоба записана в очередь: %s", path)
    return path


def process_job_file(job_path: Path, use_http: bool = False) -> int:
    """
    Обрабатывает один файл из output/image_jobs/*.json.
    use_http: True — отправлять на GENERATOR_URL, False — писать в image_queue/.
    Возвращает количество отправленных джоб.
    """
    with open(job_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    post_id = str(data.get("post_id", job_path.stem))
    images = data.get("images", [])
    sent = 0
    for i, item in enumerate(images):
        payload = job_spec_to_payload(item, post_id, i)
        if use_http:
            if send_job_to_http(payload):
                sent += 1
        else:
            send_job_to_queue(payload)
            sent += 1
    return sent


def run(use_http: bool = False, limit: int | None = None) -> int:
    """
    Сканирует output/image_jobs/, обрабатывает все (или limit) JSON-файлов.
    use_http: отправлять на локальный генератор по HTTP иначе — в очередь.
    """
    if not JOBS_DIR.exists():
        logger.warning("Папка джоб не найдена: %s", JOBS_DIR)
        return 0
    files = sorted(JOBS_DIR.glob("*.json"))
    if limit:
        files = files[:limit]
    total = 0
    for path in files:
        total += process_job_file(path, use_http=use_http)
    return total


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Отправка джоб картинок в очередь или на генератор")
    parser.add_argument("--http", action="store_true", help="Отправлять на image_generator_url")
    parser.add_argument("-n", "--limit", type=int, default=None, help="Макс. файлов из image_jobs")
    args = parser.parse_args()
    n = run(use_http=args.http, limit=args.limit)
    print(f"Обработано джоб: {n}")
