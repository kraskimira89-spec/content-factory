"""
Очищает .md файлы в output/aroma: убирает мусор с сайта Gloryon,
приводит структуру к единому виду.

Важно: запускать на оригинальных файлах (с ###). Если файлы уже очищены,
скрипт сохраняет структуру. Для повторной полноценной очистки — восстановите
оригиналы из git и запустите один раз.

Единая структура:
# Название
Код | Страна | Образ
[Gloryon](url)

## Описание
## Состав
## Применение
## Когда поможет
## Противопоказания

Запуск: python scripts/clean_aroma_md.py
"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AROMA_DIR = PROJECT_ROOT / "output" / "aroma"

# Блоки для удаления (regex)
JUNK_PATTERNS = [
    r"ПРОДУКЦИЯ\s*\n\s*ДИАГНОСТИКА\s*\n\s*БИЗНЕС\s*\n\s*НОЯБРЬСК.*?(?=\n\n|\n###|\Z)",
    r"^\s*0\s*$",
    r"^\s*\d{1,3}\s*$",  # одиночные цифры (счётчик отзывов)
    r"Аптека Бодрости Эфирные масла Gloris Aroma.*?В корзину",
    r"Код продукта — \d+\s*\n\s*\d+ руб.*?В корзину",
    r"Презентация\s*\n\s*Описание\s*\n\s*Состав\s*\n.*?Истории\s*\d*",
    r"ТАКЖЕ РЕКОМЕНДУЕМ:.*?(?=\n###|\n\n\n|\Z)",
    r"Приглашаем Лидеров\s*\n\s*Благотворительность.*?8 800 200-55-88",
    r"русский\s*\n\s*азербайджанский.*?эстонский",
    r"Адрес: г\. Новосибирск.*?Обязательна\.?\s*",
    r"ООО \"Глорион\".*?Обязательна\.?\s*",
    r"Поделись ссылкой на карточку товара\s*\n\s*копировать ссылку",
    r"image/svg\+xml\s*\n\s*Подписывайтесь на наш канал.*?Продуктах Gloryon!",
]


def _strip_junk(text: str) -> str:
    """Удаляет типовой мусор."""
    for pat in JUNK_PATTERNS:
        text = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)
    # Лишние пустые строки
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"^\s*\n+", "", text)
    return text.strip()


def _extract_section(content: str, header: str) -> str:
    """Извлекает содержимое секции между ###/## Header и следующим ###/##."""
    for prefix in (r"###", r"##"):
        pat = rf"{prefix}\s*{re.escape(header)}\s*\n(.*?)(?=\n(?:###|##)\s|\Z)"
        m = re.search(pat, content, re.DOTALL)
        if m:
            return _strip_junk(m.group(1).strip())
    return ""


def _extract_application(content: str) -> str:
    """Применение — может быть в Презентации или отдельно."""
    for h in ("Применение", "Презентация"):
        block = _extract_section(content, h)
        # Ищем блок "Как использовать" / "Как использовать:"
        use = re.search(
            r"(?:Как использовать|КАК ИСПОЛЬЗОВАТЬ)[:\s]*(.*?)(?=Противопоказания|Целебное|Косметическое|Магическое|\Z)",
            block,
            re.DOTALL | re.IGNORECASE
        )
        if use:
            s = use.group(1).strip()
            s = re.sub(r"\n{3,}", "\n\n", s)
            return s
    return ""


def _extract_contraindications(content: str) -> str:
    """Противопоказания."""
    full = content
    m = re.search(r"Противопоказания[:\s]*([^.]+?)(?=\n\n|\Z)", full, re.DOTALL | re.IGNORECASE)
    if m:
        return _strip_junk(m.group(1).strip())
    return ""


def _extract_when_helps(content: str) -> str:
    """Когда поможет — только буллеты, без Целебное/Косметическое."""
    for pat in [
        r"(?:Когда поможет|Когда пригодится|В каких случаях вам поможет[^?]*\?)\s*\n(.*?)(?=\n(?:Целебное|Косметическое|Магическое|Дополнительные|Как использовать|###)|\Z)",
        r"Кому нужно[^:\n]*:\s*\n(.*?)(?=\n(?:Целебное|Дополнительные|Как использовать|###)|\Z)",
    ]:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            s = m.group(1).strip()
            # Берём только пункты-буллеты (начинаются с "Когда", "Если", "При", "В ")
            lines = []
            for line in s.splitlines():
                line = line.strip()
                if not line or line in ("0", "Кому нужно", "эфирное масло", "«Апельсин»?"):
                    continue
                if re.match(r"^(Когда|Если|При|В |Для )", line, re.I) or (line.endswith(".") and len(line) < 120):
                    lines.append(line)
            if lines:
                return "\n".join(lines)
    return ""


def process_file(path: Path) -> str | None:
    """
    Обрабатывает один файл, возвращает очищенный текст.
    Возвращает None, если файл уже в целевом формате (пропустить перезапись).
    """
    raw = path.read_text(encoding="utf-8")
    # Файл уже очищен (нет ###, есть ##) — лёгкая доработка, не перезаписывать
    if "### " not in raw and ("## Состав" in raw or "## Описание" in raw):
        text = re.sub(r"\n{4,}", "\n\n", raw)
        return text.strip() + "\n"
    lines = raw.splitlines()

    # Заголовок и мета (первые 6 строк)
    title = ""
    meta = ""
    link = ""
    for i, line in enumerate(lines[:8]):
        if line.strip().startswith("# "):
            title = line.strip()
        elif line.startswith("Код:"):
            meta = line.strip()
        elif line.strip().startswith("[Gloryon]"):
            link = line.strip()

    # URL для ссылки
    url_match = re.search(r"\((https://[^)]+)\)", raw)
    url = url_match.group(1) if url_match else ""

    description = _extract_section(raw, "Описание")
    if not description:
        description = _extract_section(raw, "Презентация")
    # Обрезаем описание перед Целебное/Косметическое (они дублируются)
    description = re.sub(r"\n(Целебное действие|Косметическое действие|Магическое действие).*", "", description, flags=re.DOTALL)

    composition = _extract_section(raw, "Состав")
    application = _extract_application(raw)
    when = _extract_when_helps(raw)
    contra = _extract_contraindications(raw)

    # Очищаем блоки от оставшегося мусора
    def clean_block(s: str) -> str:
        if not s:
            return ""
        s = re.sub(r"^\s*0\s*\n", "", s)
        s = re.sub(r"Аптека Бодрости.*?В корзину", "", s, flags=re.DOTALL)
        s = re.sub(r"ТАКЖЕ РЕКОМЕНДУЕМ:.*", "", s, flags=re.DOTALL)
        s = re.sub(r"Приглашаем Лидеров.*", "", s, flags=re.DOTALL)
        s = re.sub(r"8 800 200-55-88.*", "", s, flags=re.DOTALL)
        s = re.sub(r"Адрес:.*Глорион.*", "", s, flags=re.DOTALL)
        s = re.sub(r"\n{3,}", "\n\n", s).strip()
        return s

    description = clean_block(description)
    composition = clean_block(composition)
    application = clean_block(application)
    when = clean_block(when)
    contra = clean_block(contra)

    # Финальная очистка: убрать ### заголовки и "0"
    def drop_invalid(s: str) -> str:
        lines = [x for x in s.splitlines() if not re.match(r"^\s*###\s", x) and x.strip() != "0"]
        return "\n".join(lines).strip()

    description = drop_invalid(description)
    composition = drop_invalid(composition)
    application = drop_invalid(application)
    when = drop_invalid(when)
    contra = drop_invalid(contra)

    # Собираем итог
    out = []
    out.append(title or "# Масло")
    out.append("")
    if meta:
        out.append(meta)
        out.append("")
    if url:
        out.append(f"[Gloryon]({url})")
        out.append("")
    out.append("---")
    out.append("")

    if description:
        out.append("## Описание")
        out.append("")
        out.append(description)
        out.append("")

    if composition:
        out.append("## Состав")
        out.append("")
        out.append(composition)
        out.append("")

    if application:
        out.append("## Применение")
        out.append("")
        out.append(application)
        out.append("")

    if when:
        out.append("## Когда поможет")
        out.append("")
        out.append(when)
        out.append("")

    if contra:
        out.append("## Противопоказания")
        out.append("")
        out.append(contra)

    return "\n".join(out).strip() + "\n"


def main():
    if not AROMA_DIR.exists():
        print(f"Папка не найдена: {AROMA_DIR}")
        return

    skip = {"catalog_10900.md", "ПРОДУКЦИЯ.md"}
    done = 0
    for f in sorted(AROMA_DIR.glob("*.md")):
        if f.name in skip:
            print(f"  [skip] {f.name}")
            continue
        try:
            cleaned = process_file(f)
            f.write_text(cleaned, encoding="utf-8")
            print(f"  [ok] {f.name}")
            done += 1
        except Exception as e:
            print(f"  [err] {f.name}: {e}")

    print(f"\n[OK] Обработано: {done}")


if __name__ == "__main__":
    main()
