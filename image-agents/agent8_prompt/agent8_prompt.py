# image-agents/agent8_prompt — генератор промптов для картинок (agent8_images_planner)
"""
На вход: готовый текст поста + метаданные (ниша, тип услуги, тон, ключевые смыслы).
На выход: JSON по image_protocol: images: [{ prompt, style, alt }, ...] (1–3 шт по count.min/max).
"""
import json
import sys
from pathlib import Path

_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent
PROMPT_FILE = PROJECT_ROOT / "prompts" / "agent_images_system.txt"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "seo-agents") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "seo-agents"))
from scripts.shared_config import get_image_protocol  # noqa: E402
from shared.api_client import ask_ai  # noqa: E402


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def build_user_message(post_text: str, metadata: dict) -> str:
    """Текст поста + JSON метаданных (тип услуги, аудитория, тон, формат)."""
    proto = get_image_protocol()
    count = proto.get("count") or {}
    min_count = count.get("min", 1)
    max_count = count.get("max", 3)
    meta_str = json.dumps(metadata, ensure_ascii=False, indent=2)
    return f"""Текст поста:

{post_text}

---

Метаданные (JSON):

{meta_str}

Сгенерируй промпты для изображений в формате JSON: поле "images" — массив объектов с полями "prompt", "style", "alt" (от {min_count} до {max_count} штук). Дополнительно можно указать общие "style", "safety_notes"."""


def run(post_text: str, metadata: dict) -> dict:
    """
    Возвращает: { "prompts": [...], "style": "...", "safety_notes": "...", "suggested_alt_texts": [...] }.
    """
    system = load_system_prompt()
    user = build_user_message(post_text, metadata)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    raw = ask_ai(messages, max_tokens=1500)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Агент 8: генерация промптов для картинок")
    parser.add_argument("--text", type=str, help="Путь к .md с текстом поста или текст")
    parser.add_argument("--meta", type=str, default="{}", help="JSON метаданных")
    args = parser.parse_args()
    if args.text and Path(args.text).is_file():
        post_text = Path(args.text).read_text(encoding="utf-8")
    else:
        post_text = args.text or "Пример текста поста о прессотерапии."
    meta = json.loads(args.meta)
    result = run(post_text, meta)
    print(json.dumps(result, ensure_ascii=False, indent=2))
