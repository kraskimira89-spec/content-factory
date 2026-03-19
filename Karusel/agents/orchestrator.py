"""
Оркестратор пайплайна карусели: Vision (опц.) → Parser → Rembg → Composer → Builder → Sender.
Поддержка async run() со статусами в чате и cleanup temp/{session_id}.
"""
import asyncio
import shutil
import sys
from pathlib import Path
from typing import Callable, Awaitable

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))

from models.carousel_schema import CarouselData

from agents.agent1_parser import parse_carousel_from_brief
from agents.agent3_rembg import process_photo_for_character
from agents.agent4_composer import compose_slides
from agents.agent5_builder import build_carousel_async, _load_preset
from logger import get_logger

logger = get_logger("orchestrator")

# Папка temp относительно корня Karusel
TEMP_BASE = _KARUSEL_ROOT / "temp"


async def _update_status(
    update_status_fn: Callable[[str], Awaitable[None]] | None,
    text: str,
) -> None:
    if update_status_fn:
        try:
            await update_status_fn(text)
        except Exception as e:
            logger.warning("Обновление статуса: %s", e)


async def run(
    *,
    photo_paths: list[str | Path],
    raw_text: str,
    user_id: int,
    session_id: str,
    bot,
    status_msg_id: int,
    run_vision: bool = False,
    preset_path: str | Path | None = None,
) -> bool:
    """
    Асинхронный пайплайн с обновлением одного статус-сообщения в чате.
    Фото уже лежат в temp/{session_id}/. Слайды сохраняются в temp/{session_id}/slides/.
    В конце вызывается Sender (альбом + меню) и cleanup temp/{session_id}.
    """
    temp_dir = TEMP_BASE / session_id
    output_dir = temp_dir / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    photo_paths = [Path(p) for p in photo_paths]

    async def update_status(text: str):
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=status_msg_id,
            text=text,
        )

    try:
        # Шаг 2 — Vision (опционально)
        await _update_status(update_status, "⏳ Анализирую фотографии…")
        vision_results = None
        if run_vision:
            try:
                from agents.agent2_vision import analyze_photos
                vision_results = analyze_photos([str(p) for p in photo_paths])
            except Exception as e:
                logger.warning("Agent 2 (Vision) пропущен: %s", e)

        # Шаг 3 — Parser
        await _update_status(update_status, "📝 Формирую структуру…")
        carousel_data = parse_carousel_from_brief(raw_text, photo_count=len(photo_paths))

        # Шаг 4 — Rembg (character_box из preset при наличии)
        await _update_status(update_status, "✂️ Обрабатываю изображения…")
        preset = _load_preset(preset_path)
        character_box = preset.get("character_box") if preset else None
        character_png_by_index = {}
        for slide in carousel_data.slides:
            if not slide.use_character:
                continue
            idx = slide.photo_index
            if idx in character_png_by_index or idx >= len(photo_paths):
                continue
            try:
                png_path = process_photo_for_character(
                    photo_paths[idx],
                    output_dir=temp_dir / "chars",
                    character_box=character_box,
                )
                character_png_by_index[idx] = png_path
            except Exception as e:
                logger.warning("Rembg для фото %s: %s", photo_paths[idx].name, e)

        # Шаг 5 — Composer
        await _update_status(update_status, "🎨 Собираю слайды…")
        slides_data = compose_slides(
            carousel_data,
            photo_paths,
            character_png_by_photo_index=character_png_by_index or None,
            vision_results=vision_results,
        )

        # Шаг 6 — Builder (параллельно, preset для viewport/layout)
        await _update_status(update_status, "🖼 Рендерю карусель…")
        slide_jpg_paths = await build_carousel_async(
            slides_data,
            carousel_data.brand,
            output_dir,
            preset_path=preset_path,
        )

        # Шаг 7 — Sender (альбом + меню)
        await _update_status(update_status, "📤 Отправляю…")
        from agents.agent6_poster import send_album_with_menu
        await send_album_with_menu(
            bot=bot,
            user_id=user_id,
            slide_paths=slide_jpg_paths,
            brand=carousel_data.brand,
        )

        return True
    except Exception as e:
        logger.exception("Оркестратор: %s", e)
        try:
            await bot.send_message(
                user_id,
                f"❌ Ошибка: {e}\nПопробуй ещё раз или /start",
            )
        except Exception:
            pass
        return False
    finally:
        if temp_dir.is_dir():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning("Cleanup %s: %s", temp_dir, e)


def run_pipeline(
    photo_paths: list[str | Path],
    brief_text: str,
    output_dir: str | Path,
    *,
    run_vision: bool = False,
    run_poster: bool = False,
    bot=None,
    chat_id: int | None = None,
    design_tokens_path: str | Path | None = None,
    figma_map_path: str | Path | None = None,
    preset_path: str | Path | None = None,
) -> list[str]:
    """
    Синхронный пайплайн (для CLI и обратной совместимости).
    Если run_poster и bot/chat_id заданы — отправляет альбом без меню (post_to_telegram).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    photo_paths = [Path(p) for p in photo_paths]
    for p in photo_paths:
        if not p.is_file():
            raise FileNotFoundError(f"Фото не найдено: {p}")

    logger.info("Agent 1: парсинг ТЗ")
    carousel_data = parse_carousel_from_brief(brief_text, photo_count=len(photo_paths))

    vision_results = None
    if run_vision:
        try:
            from agents.agent2_vision import analyze_photos
            vision_results = analyze_photos([str(p) for p in photo_paths])
        except Exception as e:
            logger.warning("Agent 2 (Vision) пропущен: %s", e)

    preset = _load_preset(preset_path)
    character_box = preset.get("character_box") if preset else None
    character_png_by_index = {}
    for slide in carousel_data.slides:
        if not slide.use_character:
            continue
        idx = slide.photo_index
        if idx in character_png_by_index or idx >= len(photo_paths):
            continue
        try:
            png_path = process_photo_for_character(
                photo_paths[idx],
                output_dir=output_dir / "chars",
                character_box=character_box,
            )
            character_png_by_index[idx] = png_path
        except Exception as e:
            logger.warning("Rembg для фото %s: %s", photo_paths[idx].name, e)

    logger.info("Agent 4: композиция слайдов")
    slides_data = compose_slides(
        carousel_data,
        photo_paths,
        character_png_by_photo_index=character_png_by_index or None,
        vision_results=vision_results,
    )

    logger.info("Agent 5: сборка слайдов")
    slide_jpg_paths = asyncio.run(
        build_carousel_async(
            slides_data,
            carousel_data.brand,
            output_dir,
            design_tokens_path=design_tokens_path,
            figma_map_path=figma_map_path,
            preset_path=preset_path,
        )
    )

    if run_poster and bot is not None and chat_id is not None:
        try:
            from agents.agent6_poster import post_to_telegram
            asyncio.run(post_to_telegram(bot, chat_id, slide_jpg_paths))
        except Exception as e:
            logger.warning("Agent 6 (Poster) ошибка: %s", e)

    return slide_jpg_paths
