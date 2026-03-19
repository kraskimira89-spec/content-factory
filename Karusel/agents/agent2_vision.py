"""
Agent 2 — Vision: анализ фото через LLM с vision (GPT-4o или аналог).
Для каждого фото возвращает has_person, photo_quality, recommended_use и т.д.
При отсутствии vision API возвращает fallback (все фото как raw/medium).
"""
import base64
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
_PROJECT_ROOT = _KARUSEL_ROOT.parent
_ENV_PATH = _PROJECT_ROOT / "config" / ".env"
load_dotenv(_ENV_PATH)

VISION_PROMPT = """Проанализируй фото и верни СТРОГО один JSON без markdown:
{
  "has_person": true/false,
  "person_position": "center|left|right",
  "background_type": "studio|interior|outdoor|equipment",
  "photo_quality": "high|medium|low",
  "recommended_use": "character_slide|raw_photo|background",
  "suggested_slide_type": "cover|benefits|photo_raw"
}
Верни ТОЛЬКО JSON."""

if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger
logger = get_logger("agent2_vision")


def _get_openai_client_with_vision():
    """Клиент с поддержкой vision (OpenAI-совместимый). Perplexity может не поддерживать image."""
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        if not api_key:
            return None, None
        return OpenAI(api_key=api_key, base_url=base_url), model
    except Exception as e:
        logger.warning("Vision client init: %s", e)
        return None, None


def _image_to_data_uri(path: str | Path) -> str:
    """Читает файл и возвращает data URI для вставки в content."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64,{b64}"


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        return m.group(1).strip()
    return raw


def analyze_one_photo(image_path: str | Path) -> dict:
    """Анализирует одно фото через vision API. При ошибке возвращает fallback dict."""
    client, model = _get_openai_client_with_vision()
    if not client:
        return {
            "has_person": False,
            "person_position": "center",
            "background_type": "interior",
            "photo_quality": "medium",
            "recommended_use": "raw_photo",
            "suggested_slide_type": "photo_raw",
        }
    try:
        data_uri = _image_to_data_uri(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ]
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
        )
        text = resp.choices[0].message.content or "{}"
        data = json.loads(_extract_json(text))
        return {
            "has_person": data.get("has_person", False),
            "person_position": data.get("person_position", "center"),
            "background_type": data.get("background_type", "interior"),
            "photo_quality": data.get("photo_quality", "medium"),
            "recommended_use": data.get("recommended_use", "raw_photo"),
            "suggested_slide_type": data.get("suggested_slide_type", "photo_raw"),
        }
    except Exception as e:
        logger.warning("Vision для %s: %s", Path(image_path).name, e)
        return {
            "has_person": False,
            "person_position": "center",
            "background_type": "interior",
            "photo_quality": "medium",
            "recommended_use": "raw_photo",
            "suggested_slide_type": "photo_raw",
        }


def analyze_photos(photo_paths: list[str | Path]) -> list[dict]:
    """Анализирует каждое фото, возвращает list[dict] по одному на фото."""
    return [analyze_one_photo(p) for p in photo_paths]
