"""
Логирование Karusel: все логи в папке Karusel/logs/.
Один файл karusel.log с ротацией, общий для бота и агентов.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

KARUSEL_ROOT = Path(__file__).resolve().parent
LOG_DIR = KARUSEL_ROOT / "logs"
LOG_FILE = LOG_DIR / "karusel.log"

_CONFIGURED = False


def _setup():
    global _CONFIGURED
    if _CONFIGURED:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2 * 1024 * 1024,  # 2 МБ
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger("karusel")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с именем karusel.<name>. Пишет в Karusel/logs/karusel.log."""
    _setup()
    if not name.startswith("karusel."):
        name = f"karusel.{name}"
    return logging.getLogger(name)
