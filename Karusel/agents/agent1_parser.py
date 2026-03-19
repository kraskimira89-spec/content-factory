"""
Agent 1 — Parser: текст ТЗ → JSON структура карусели (CarouselData).
Использует seo-agents/shared/api_client.ask_ai().
"""
import json
import os
import re
import sys
from pathlib import Path

# Корень content-factory и путь к seo-agents/shared
_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
_PROJECT_ROOT = _KARUSEL_ROOT.parent
_SHARED_DIR = _PROJECT_ROOT / "seo-agents" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from api_client import ask_ai  # type: ignore

# Модели и логгер карусели
sys.path.insert(0, str(_KARUSEL_ROOT))
from models.carousel_schema import CarouselData, Brand, SlideData
from logger import get_logger

PROMPT_FILE = _KARUSEL_ROOT / "prompts" / "agent1_parser.txt"
logger = get_logger("agent1_parser")


def load_system_prompt(photo_count: int) -> str:
    """Загружает системный промпт и подставляет photo_count."""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    return text.replace("{photo_count}", str(photo_count))


def _extract_json(raw: str) -> str:
    """Достаёт JSON из ответа (убирает markdown-обёртку если есть)."""
    raw = raw.strip()
    # Убрать ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        return m.group(1).strip()
    return raw


def parse_carousel_from_brief(brief_text: str, photo_count: int) -> CarouselData:
    """
    По тексту ТЗ и количеству фото возвращает валидную CarouselData.
    """
    system = load_system_prompt(photo_count)
    user = f"ТЗ от пользователя:\n{brief_text}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    response = ask_ai(messages, max_tokens=2000)
    json_str = _extract_json(response)
    data = json.loads(json_str)
    # Нормализация: slides могут содержать лишние поля для composer
    brand = data.get("brand", {})
    slides_raw = data.get("slides", [])
    slides = []
    for s in slides_raw:
        slides.append({
            "id": s.get("id", len(slides) + 1),
            "type": s.get("type", "benefits"),
            "title": s.get("title", ""),
            "subtitle": s.get("subtitle", ""),
            "bullets": s.get("bullets", []),
            "closing_line": s.get("closing_line", ""),
            "photo_index": s.get("photo_index", 0),
            "use_character": s.get("use_character", False),
            "character_position": s.get("character_position", "right"),
            "need_icons": s.get("need_icons", False),
            "icon_hints": s.get("icon_hints", []),
        })
    return CarouselData(
        brand=Brand(
            name=brand.get("name", ""),
            city=brand.get("city", ""),
            phone=brand.get("phone", ""),
            service=brand.get("service", ""),
        ),
        slides=[SlideData(**s) for s in slides],
    )


if __name__ == "__main__":
    # Мини-тест: только парсинг по тексту
    brief = """
    Услуга: Массаж. Город: Москва. Телефон: +7 999 123-45-67.
    Название центра: Центр Энтузиаст.
    Нужна карусель: обложка с врачом, преимущества массажа, показания, как проходит, кому полезно, результаты, фото кабинета, призыв записаться.
    """
    result = parse_carousel_from_brief(brief, photo_count=5)
    print(result.model_dump_json(indent=2))
