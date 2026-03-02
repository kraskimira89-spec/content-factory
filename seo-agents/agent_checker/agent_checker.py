"""
Агент-проверяющий страницу услуги по эталонному чек-листу.

Вход:
  - Название услуги
  - Текст/HTML страницы (файл, URL или stdin)

Выход:
  - Таблица блоков: статус (есть/нет/частично) + комментарий
  - Рекомендации по доработке (5–10 пунктов)

Использование:
  python seo-agents/agent_checker/agent_checker.py --service "ВЛОК" --file output/page.html
  python seo-agents/agent_checker/agent_checker.py --service "Массаж" --url http://91.229.11.147/uslugi/massazh/
  python seo-agents/agent_checker/agent_checker.py --service "Соляная комната"  # stdin
"""

import argparse
import os
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent_checker.txt")
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

from api_client import ask_ai  # type: ignore
from logger import get_logger  # type: ignore

logger = get_logger("seo_agents.agent_checker")


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def fetch_page_html(url: str) -> str:
    """Загружает HTML страницы по URL."""
    try:
        import requests
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        raise RuntimeError(f"Не удалось загрузить страницу {url}: {e}") from e


def load_content(source: str | None, file_path: str | None, url: str | None) -> str:
    """Загружает контент из файла, URL или stdin."""
    if url:
        return fetch_page_html(url)
    if file_path:
        path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if source:
        return source
    # stdin
    if sys.stdin.isatty():
        print("Вставь HTML/текст страницы (Ctrl+Z, Enter — завершить на Windows):", file=sys.stderr)
    return sys.stdin.read()


def build_user_message(service_name: str, content: str, audience_hint: str | None) -> str:
    parts = [
        f"Услуга: **{service_name}**",
        "",
        "Текст/HTML страницы:",
        "---",
        content[:15000],  # лимит, чтобы не перегружать контекст
        "---",
        "",
        "Проверь страницу по эталонному чек-листу. Верни таблицу блоков и рекомендации.",
    ]
    if audience_hint:
        parts.insert(2, f"Целевая аудитория (подсказка): {audience_hint}")
        parts.insert(3, "")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Агент-проверяющий страницу услуги по чек-листу блоков"
    )
    parser.add_argument("--service", "-s", required=True, help="Название услуги")
    parser.add_argument("--file", "-f", help="Путь к файлу с HTML/текстом страницы")
    parser.add_argument("--url", "-u", help="URL страницы (загрузка по HTTP)")
    parser.add_argument("--audience", "-a", help="Краткое описание ЦА (опционально)")
    parser.add_argument("--output", "-o", help="Сохранить отчёт в файл")
    args = parser.parse_args()

    try:
        content = load_content(None, args.file, args.url)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    if not content or not content.strip():
        print("Ошибка: контент страницы пуст.", file=sys.stderr)
        sys.exit(1)

    print("Проверяю страницу...", file=sys.stderr)
    logger.info("agent_checker: service=%s, content_len=%d", args.service, len(content))

    system_prompt = load_system_prompt()
    user_message = build_user_message(args.service, content, args.audience)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    report = ask_ai(messages, max_tokens=2500)
    logger.info("agent_checker: report length=%d", len(report))

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Отчёт сохранён: {out_path}", file=sys.stderr)

    print(report)


if __name__ == "__main__":
    main()
