# keywords_db: хранение ключевых фраз (файловая версия без PostgreSQL)
# Agent1 сохраняет, Agent2/Agent3 загружают по паре (услуга, город)

import os
from pathlib import Path

# Корень проекта
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_OUTPUT_DIR = _PROJECT_ROOT / "output"


def _safe(service: str, city: str) -> tuple[str, str]:
    return service.replace(" ", "_"), city.replace(" ", "_")


def save_keywords(service_name: str, city: str, keywords_text: str) -> None:
    """Сохраняет ключи в файл (agent1 уже сохраняет в output; здесь дублируем в .keywords_cache для load)."""
    # Agent1 сам пишет в output с timestamp. Для load ищем по маске — доп. файл не нужен.
    # Сохранение в output делает agent1.save_keywords(). Эта функция — заглушка для БД.
    pass


def load_keywords(service_name: str, city: str) -> str | None:
    """Загружает последние ключи по услуге и городу из output/*_keywords_*_*.txt."""
    safe_s, safe_c = _safe(service_name, city)
    pattern = f"*_keywords_{safe_s}_{safe_c}.txt"
    import glob

    files = sorted(
        glob.glob(str(_OUTPUT_DIR / pattern)),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    if not files:
        return None
    return Path(files[0]).read_text(encoding="utf-8")
