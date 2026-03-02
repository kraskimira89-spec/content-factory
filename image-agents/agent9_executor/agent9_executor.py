# image-agents/agent9_executor — вызов локального генератора, сохранение по image_protocol
"""
На вход: один промпт (+ style, slug, alt, index).
Действие: POST в локальный движок (image_generator_url), сохраняет в storage_root по relative_path_pattern.
На выход: { "image_path": "images/2026/03/slug-1.jpg", "alt": "..." } (путь относительно storage_root).
"""
import json
import sys
from pathlib import Path

import requests

_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.shared_config import (
    build_image_relative_path,
    get_config,
    get_image_storage_root,
)  # noqa: E402

_IMG = get_config().get("image_agents", {})
GENERATOR_URL = _IMG.get("image_generator_url", "http://localhost:7860/generate")
TIMEOUT = _IMG.get("image_generator_timeout_sec", 120)


def _fetch_image(prompt: str, style: str = "") -> bytes:
    """
    Отправляет промпт в локальный генератор. Ожидает ответ — бинарное изображение (image/png или image/jpeg).
    Если API возвращает JSON с base64 — можно расширить.
    """
    payload = {"prompt": prompt}
    if style:
        payload["style"] = style
    resp = requests.post(GENERATOR_URL, json=payload, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"Генератор вернул {resp.status_code}: {resp.text[:500]}")
    ct = resp.headers.get("Content-Type", "")
    if "application/json" in ct:
        data = resp.json()
        import base64
        b64 = data.get("image") or data.get("image_base64") or data.get("b64")
        if b64:
            return base64.b64decode(b64)
        raise RuntimeError("Ответ генератора: JSON без image/base64")
    return resp.content


def run(
    prompt: str,
    slug: str = "img",
    alt: str = "",
    style: str = "",
    index: int = 1,
) -> dict:
    """
    Генерирует одну картинку, сохраняет в storage_root по relative_path_pattern.
    Возвращает { "image_path": "images/2026/03/slug-1.jpg", "alt": "..." } (относительно storage_root).
    """
    image_bytes = _fetch_image(prompt, style)
    storage_root = get_image_storage_root()
    relative_path = build_image_relative_path(slug, index)
    full_path = (storage_root / relative_path).resolve()
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(image_bytes)
    return {"image_path": relative_path.replace("\\", "/"), "alt": alt or slug}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Агент 9: генерация одной картинки, сохранение в media/images")
    parser.add_argument("prompt", nargs="?", default="Cozy wellness room, soft light, modern interior", help="Промпт для генератора")
    parser.add_argument("--slug", default="img", help="Префикс имени файла")
    parser.add_argument("--alt", default="", help="Alt-текст для изображения")
    parser.add_argument("--style", default="", help="Стиль (передаётся в генератор)")
    parser.add_argument("--index", type=int, default=1, help="Индекс картинки для шаблона пути (relative_path_pattern)")
    args = parser.parse_args()
    result = run(args.prompt, slug=args.slug, alt=args.alt, style=args.style, index=args.index)
    print(json.dumps(result, ensure_ascii=False))
