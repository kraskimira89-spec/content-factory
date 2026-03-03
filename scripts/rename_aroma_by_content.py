"""
Переименовывает .md и .pdf в output/aroma по содержимому.

- .md: по первому заголовку (# ...)
- .pdf: по извлечённому тексту (имя масла или код из KNOWN_OILS)

Запуск: python scripts/rename_aroma_by_content.py
"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AROMA_DIR = PROJECT_ROOT / "output" / "aroma"

CODE_TO_NAME = {
    "00884": "Пихтовая_хвоя", "00863": "Апельсин_сладкий", "00851": "Бергамот",
    "00865": "Ваниль_(масляный_экстракт)", "00852": "Герань", "00853": "Грейпфрут",
    "00854": "Иланг-иланг", "00859": "Лаванда", "00861": "Лимон",
    "00869": "Можжевельник", "00862": "Мята_перечная", "00868": "Мандарин",
    "00864": "Пальмароза", "00866": "Петитгрейн", "00857": "Розмарин",
    "00860": "Чайное_дерево", "00855": "Кедровое_дерево", "00858": "Эвкалипт",
}

OIL_NAMES = [
    "Пихтовая хвоя", "Апельсин сладкий", "Бергамот", "Ваниль", "Герань", "Грейпфрут",
    "Иланг-иланг", "Лаванда", "Лимон", "Можжевельник", "Мята перечная", "Мандарин",
    "Пальмароза", "Петитгрейн", "Розмарин", "Чайное дерево", "Кедровое дерево", "Эвкалипт",
]


def _sanitize_filename(name: str) -> str:
    s = re.sub(r"[<>:\"|?*\\/]", "_", name)
    s = re.sub(r"\s+", "_", s).strip("_")[:80]
    return s or "untitled"


def _get_title_from_md(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return None


def _extract_text_from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return " ".join(p.extract_text() or "" for p in reader.pages[:3])
    except Exception:
        return ""


def _get_title_from_pdf(path: Path) -> str | None:
    text = _extract_text_from_pdf(path)
    if not text or len(text) < 10:
        return None
    for name in OIL_NAMES:
        if name in text:
            stem = path.stem
            suffix_match = re.match(r"^\d+_(\d+)$", stem)
            if suffix_match:
                num = suffix_match.group(1)
                return f"{_sanitize_filename(name)}_{num}"
            return _sanitize_filename(name)
    code_match = re.match(r"^(\d{5})_(\d+)$", path.stem)
    if code_match:
        code, num = code_match.groups()
        base = CODE_TO_NAME.get(code, code)
        return f"{base}_{num}"
    return None


def main():
    if not AROMA_DIR.exists():
        print(f"Папка не найдена: {AROMA_DIR}")
        return

    renamed = 0
    for f in sorted(AROMA_DIR.iterdir()):
        if f.name == "catalog_10900.md":
            continue

        if f.suffix.lower() == ".md":
            title = _get_title_from_md(f)
        elif f.suffix.lower() == ".pdf":
            title = _get_title_from_pdf(f)
        else:
            continue

        if not title:
            print(f"  [skip] {f.name} — не удалось извлечь название")
            continue

        new_name = _sanitize_filename(title) + f.suffix
        new_path = f.parent / new_name
        if f.name == new_name:
            continue
        if new_path.exists() and new_path != f:
            print(f"  [skip] {f.name} — {new_name} уже существует")
            continue
        f.rename(new_path)
        print(f"  {f.name} -> {new_name}")
        renamed += 1

    print(f"\n[OK] Переименовано: {renamed}")


if __name__ == "__main__":
    main()
