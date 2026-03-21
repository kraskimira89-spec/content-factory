"""
Agent 4 — Composer: сопоставляет слайды с персонажами, фоном и иконками.
Вход: CarouselData (Agent 1), результаты Vision (опционально), пути к PNG персонажей (Agent 3).
Выход: list[dict] с полными данными для Builder (character_png, bg_photo, photo_path и т.д.).
"""
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
_ASSETS_ICONS = _KARUSEL_ROOT / "assets" / "carousel" / "icons"
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger
logger = get_logger("agent4_composer")


def _pick_best_character_index(vision_results: list[dict] | None) -> int:
    """Выбирает индекс фото с лучшим качеством персонажа."""
    if not vision_results:
        return 0
    scored = [
        (i, r)
        for i, r in enumerate(vision_results)
        if r.get("has_person") and r.get("photo_quality") != "low"
    ]
    if not scored:
        return 0
    # Сортируем: high > medium
    quality_order = {"high": 2, "medium": 1}
    best = max(
        scored,
        key=lambda x: quality_order.get(x[1].get("photo_quality", ""), 0),
    )
    return best[0]


def _get_icons_for_hints(icon_hints: list[str]) -> list[str]:
    """Возвращает пути к иконкам из assets/carousel/icons по подсказкам."""
    if not _ASSETS_ICONS.is_dir():
        return []
    paths = []
    for hint in icon_hints:
        # Ищем файл с именем, содержащим hint (office.png, sport.png, ...)
        for f in _ASSETS_ICONS.iterdir():
            if f.suffix.lower() in (".png", ".svg") and hint.lower() in f.stem.lower():
                paths.append(str(f.resolve()))
                break
    return paths


CHARGEN_SKIP_SLIDE_TYPES = frozenset({"photo_raw", "cta"})


def compose_slides(
    carousel_data,
    photo_paths: list[str | Path],
    character_png_by_photo_index: dict[int, str] | None = None,
    vision_results: list[dict] | None = None,
    char_per_slide: dict[int, str] | None = None,
    char_on_every_slide: bool | None = None,
) -> list[dict]:
    """
    Готовит список слайдов с заполненными character_png, bg_photo, photo_path, icons.
    character_png_by_photo_index: маппинг photo_index -> путь к PNG персонажа (после rembg).
    char_per_slide: маппинг slide.id -> PNG (Agent 3b ComfyUI), приоритет над rembg.
    char_on_every_slide: если True — на слайдах вне photo_raw/cta пытаемся показать персонажа (rembg fallback).
    """
    if character_png_by_photo_index is None:
        character_png_by_photo_index = {}
    if char_per_slide is None:
        char_per_slide = {}
    if char_on_every_slide is None:
        try:
            from agents.agent3b_chargen import is_char_on_every_slide as _coe
            char_on_every_slide = _coe()
        except Exception:
            char_on_every_slide = False

    photo_paths = [Path(p) for p in photo_paths]
    brand = carousel_data.brand
    brand_dict = brand.model_dump() if hasattr(brand, "model_dump") else brand
    best_char_index = _pick_best_character_index(vision_results)
    composed = []
    for slide in carousel_data.slides:
        slide_dict = slide.model_dump() if hasattr(slide, "model_dump") else dict(slide)
        slide_type = slide_dict.get("type", "benefits")
        photo_index = slide_dict.get("photo_index", 0)
        use_char = slide_dict.get("use_character", False)
        slide_id = slide_dict.get("id", 0)

        in_skip = slide_type in CHARGEN_SKIP_SLIDE_TYPES
        effective_use_char = use_char or (char_on_every_slide and not in_skip)

        # Приоритет: AI (char_per_slide) > rembg > нет
        ai_path = char_per_slide.get(slide_id) if slide_id in char_per_slide else None
        if ai_path and Path(ai_path).is_file():
            slide_dict["character_png"] = ai_path
            logger.info("Слайд id=%s: персонаж из CharGen (AI)", slide_id)
        elif effective_use_char and not in_skip:
            png_path = character_png_by_photo_index.get(
                photo_index,
                character_png_by_photo_index.get(best_char_index),
            )
            if png_path and Path(png_path).is_file():
                slide_dict["character_png"] = png_path
                logger.info("Слайд id=%s: персонаж из rembg", slide_id)
            elif effective_use_char and not use_char:
                logger.warning(
                    "Слайд id=%s: ожидался персонаж (char_on_every_slide), rembg недоступен",
                    slide_id,
                )
        if slide_type == "cover" and photo_paths and 0 <= photo_index < len(photo_paths):
            # Фон обложки — можно взять одно из фото (по ТЗ опционально)
            slide_dict["bg_photo"] = str(photo_paths[0])
        if slide_type == "photo_raw" and 0 <= photo_index < len(photo_paths):
            slide_dict["photo_path"] = str(photo_paths[photo_index])
        if slide_dict.get("need_icons") and slide_dict.get("icon_hints"):
            slide_dict["icons"] = _get_icons_for_hints(slide_dict["icon_hints"])
        composed.append(slide_dict)
    return composed
