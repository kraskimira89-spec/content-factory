"""
Agent 6 — Poster: отправка слайдов альбомом в Telegram + меню действий.
"""
import asyncio
import sys
from pathlib import Path

_KARUSEL_ROOT = Path(__file__).resolve().parent.parent


def _brand_caption(brand) -> str:
    """Формирует подпись к альбому из бренда (модель или dict)."""
    if hasattr(brand, "model_dump"):
        d = brand.model_dump()
    else:
        d = dict(brand) if brand else {}
    name = d.get("name", "")
    city = d.get("city", "")
    phone = d.get("phone", "")
    parts = ["✅ Карусель готова!"]
    if name or city or phone:
        parts.append("")
        if name:
            parts.append(f"🏥 {name}")
        if city:
            parts.append(f"📍 {city}")
        if phone:
            parts.append(f"📞 {phone}")
    return "\n".join(parts)


async def send_album_with_menu(
    bot,
    user_id: int,
    slide_paths: list[str | Path],
    brand,
) -> bool:
    """
    Отправляет альбом с подписью по бренду, затем сообщение «Что делаем дальше?»
    с кнопками: Новая карусель, Опубликовать, Изменить слайд, Главное меню.
    """
    try:
        from aiogram.types import (
            FSInputFile,
            InputMediaPhoto,
            InlineKeyboardMarkup,
            InlineKeyboardButton,
        )
    except ImportError:
        raise ImportError("Установите aiogram: pip install aiogram>=3")

    if not slide_paths:
        return False
    slide_paths = [Path(p) for p in slide_paths]
    media = []
    caption = _brand_caption(brand)
    for i, path in enumerate(slide_paths):
        if not path.is_file():
            continue
        photo = FSInputFile(path)
        if i == 0:
            media.append(InputMediaPhoto(media=photo, caption=caption))
        else:
            media.append(InputMediaPhoto(media=photo))
    if not media:
        return False
    await bot.send_media_group(chat_id=user_id, media=media)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Новая карусель", callback_data="car:enter"),
            InlineKeyboardButton(text="📤 Опубликовать", callback_data="car:autopost"),
        ],
        [
            InlineKeyboardButton(text="✏️ Изменить слайд", callback_data="car:edit"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main:menu"),
        ],
    ])
    await bot.send_message(
        chat_id=user_id,
        text="Что делаем дальше?",
        reply_markup=keyboard,
    )
    return True


async def post_to_telegram(
    bot,
    chat_id: int,
    slide_paths: list[str | Path],
    caption: str = "",
) -> bool:
    """
    Отправляет карусель альбомом в TG (без меню).
    bot: экземпляр aiogram Bot.
    slide_paths: список путей к JPG.
    """
    try:
        from aiogram.types import FSInputFile, InputMediaPhoto
    except ImportError:
        raise ImportError("Установите aiogram: pip install aiogram>=3")

    if not slide_paths:
        return False
    slide_paths = [Path(p) for p in slide_paths]
    media = []
    for i, path in enumerate(slide_paths):
        if not path.is_file():
            continue
        photo = FSInputFile(path)
        if i == 0 and caption:
            media.append(InputMediaPhoto(media=photo, caption=caption))
        else:
            media.append(InputMediaPhoto(media=photo))
    if not media:
        return False
    await bot.send_media_group(chat_id=chat_id, media=media)
    return True


def post_to_telegram_sync(bot, chat_id: int, slide_paths: list[str | Path], caption: str = "") -> bool:
    """Синхронная обёртка."""
    return asyncio.run(post_to_telegram(bot, chat_id, slide_paths, caption))
