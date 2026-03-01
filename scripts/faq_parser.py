"""
Парсер FAQ из Markdown-файлов для REST API service_data.

Поддерживаемые форматы:
1. Эталон: **Вопрос?** + пустая строка + абзац ответа
2. С span: <span style="color:#ff8800">**Вопрос?**</span> + пустая строка + абзац
3. JSON: {"q":"...","a":"..."} в блоке

Использование:
  from scripts.faq_parser import parse_faq_from_md
  faq = parse_faq_from_md(md_content)
  # -> [{"q": "...", "a": "..."}, ...]
"""
import json
import re
from pathlib import Path


FAQ_HEADING = "## Часто задаваемые вопросы"
FAQ_HEADING_ALT = "### FAQ"
FAQ_HEADINGS = (FAQ_HEADING, FAQ_HEADING_ALT)


def _clean_text(s: str) -> str:
    """Убирает лишние пробелы и маркеры цитирования [1][2]."""
    if not s:
        return ""
    s = re.sub(r"\[\d+\]", "", s)
    return s.strip()


def _extract_question_from_tag(match: re.Match) -> str | None:
    """Извлекает текст вопроса из **...** или <span...>**...**</span>."""
    group = match.group(1) or match.group(2)
    if group:
        return _clean_text(group)
    return None


def parse_faq_from_md(content: str) -> list[dict]:
    """
    Находит блок «Часто задаваемые вопросы» и извлекает пары вопрос–ответ.

    Возвращает список {"q": str, "a": str}.
    """
    # Найти начало FAQ-блока
    faq_start = -1
    for heading in FAQ_HEADINGS:
        idx = content.find(heading)
        if idx >= 0:
            faq_start = idx + len(heading)
            break

    if faq_start < 0:
        return []

    # Взять текст до следующего ##
    rest = content[faq_start:]
    next_h2 = re.search(r"\n## ", rest)
    if next_h2:
        rest = rest[: next_h2.start()]

    # Попытка 1: JSON в тексте
    json_matches = re.findall(r'\{\s*"q"\s*:\s*"[^"]*"\s*,\s*"a"\s*:\s*"[^"]*"\s*\}', rest)
    if json_matches:
        try:
            result = []
            for m in json_matches:
                obj = json.loads(m)
                result.append({"q": _clean_text(obj["q"]), "a": _clean_text(obj["a"])})
            if result:
                return result
        except json.JSONDecodeError:
            pass

    # Попытка 2: <span ...>**Вопрос**</span> или **Вопрос**
    # Паттерн: span с **...** или отдельно **...**, затем пустые строки и абзац
    pairs = []
    # Разбиваем на блоки: вопрос (span/**) + пустая строка + ответ
    # Регекс: (span или **) захватывает вопрос, затем до следующего вопроса
    question_pattern = re.compile(
        r'(?:<span[^>]*>\s*\*\*([^*]+)\*\*\s*</span>|\*\*([^*]+)\*\*)',
        re.IGNORECASE,
    )

    lines = rest.split("\n")
    i = 0
    current_q = None
    current_a_lines = []

    def flush_pair():
        nonlocal current_q, current_a_lines
        if current_q and current_a_lines:
            ans = " ".join(l.strip() for l in current_a_lines if l.strip())
            if ans:
                pairs.append({"q": _clean_text(current_q), "a": _clean_text(ans)})
        current_q = None
        current_a_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Пустая строка — разделитель
        if not stripped:
            i += 1
            continue

        match = question_pattern.search(line)
        if match:
            flush_pair()
            current_q = (match.group(1) or match.group(2)).strip()
            current_a_lines = []
            i += 1
            # Собрать ответ — следующие непустые строки до следующего вопроса
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip():
                    i += 1
                    continue
                if question_pattern.search(next_line):
                    break
                current_a_lines.append(next_line)
                i += 1
            continue

        # Строка без вопроса — возможно часть ответа (если ещё нет current_q, пропускаем)
        if current_q and current_a_lines:
            # Продолжение абзаца ответа
            current_a_lines.append(line)
        i += 1

    flush_pair()
    return pairs


def parse_faq_from_file(path: Path | str) -> list[dict]:
    """Читает файл и возвращает распарсенный FAQ."""
    path = Path(path)
    if not path.is_file():
        return []
    return parse_faq_from_md(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование: python scripts/faq_parser.py <path-to.md>")
        sys.exit(1)

    p = Path(sys.argv[1])
    faq = parse_faq_from_file(p)
    print(json.dumps(faq, ensure_ascii=False, indent=2))
