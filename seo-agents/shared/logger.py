import logging
import os
from logging.handlers import RotatingFileHandler

# Базовая папка проекта
BASE_DIR = r"D:\content-factory"

# Папка для логов
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Чтобы не вешать несколько хендлеров на один и тот же логгер
_CONFIGURED_LOGGERS: set[str] = set()


def _filename_for_logger(name: str) -> str:
    """
    Определяем имя файла лога по имени логгера.
    Для агентов — отдельные файлы agent1.log / agent2.log / agent3.log.
    Остальное — в общем seo_agents.log.
    """
    suffix = name.split(".")[-1]
    if suffix in {"agent1", "agent2", "agent3"}:
        return f"{suffix}.log"
    return "seo_agents.log"


def get_logger(name: str) -> logging.Logger:
    """Возвращает настроенный логгер с ротацией и отдельными файлами для агентов."""
    logger = logging.getLogger(name)
    if name in _CONFIGURED_LOGGERS:
        return logger

    logger.setLevel(logging.INFO)

    log_file = os.path.join(LOG_DIR, _filename_for_logger(name))
    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,  # ~1 МБ на файл
        backupCount=5,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    _CONFIGURED_LOGGERS.add(name)
    return logger


