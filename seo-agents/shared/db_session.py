# db_session: последняя пара (услуга, город) для цепочки агентов (файловая версия)

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SESSION_FILE = _PROJECT_ROOT / "output" / ".last_pair"


def set_last_pair(service_name: str, city: str) -> None:
    """Сохраняет последнюю пару услуга+город."""
    _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SESSION_FILE.write_text(f"{service_name}\n{city}", encoding="utf-8")


def get_last_pair() -> tuple[str, str] | None:
    """Возвращает последнюю пару (service_name, city) или None."""
    if not _SESSION_FILE.exists():
        return None
    lines = _SESSION_FILE.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) >= 2:
        return lines[0].strip(), lines[1].strip()
    return None
