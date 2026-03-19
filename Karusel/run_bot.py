"""
Точка входа TG-бота карусели (aiogram 3).
Регистрирует callback car:enter и хэндлер ожидания фото + ТЗ.
Запуск из корня content-factory: python Karusel/run_bot.py
Логи: Karusel/logs/karusel.log
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Корень content-factory для config/.env
KARUSEL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = KARUSEL_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "config" / ".env")

# Логирование в папке бота Karusel/logs/
sys.path.insert(0, str(KARUSEL_ROOT))
from logger import get_logger
log = get_logger("bot")
# aiogram тоже пишет в Karusel/logs/karusel.log
_handler = logging.FileHandler(KARUSEL_ROOT / "logs" / "karusel.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger("aiogram").addHandler(_handler)
logging.getLogger("aiogram").setLevel(logging.INFO)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.carousel_handler import router as carousel_router


async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        log.warning("Не задан TELEGRAM_BOT_TOKEN в config/.env")
        print("Задайте TELEGRAM_BOT_TOKEN в config/.env")
        return
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(carousel_router)
    log.info("Бот запущен. Ожидаю callback car:enter для карусели.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
