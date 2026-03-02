"""
Агент-исполнитель: по отчёту первого агента (чек-лист) формирует конкретное ТЗ для копирайтера и верстальщика.

Вход:
  - Название услуги
  - Отчёт агента-checker (таблица + рекомендации) — из файла или stdin
  - (Опционально) текст/HTML страницы для контекста

Выход:
  - ТЗ по тексту (копирайтеру)
  - ТЗ по верстке (кодеру)
  - Приоритеты задач

Использование:
  # Цепочка: checker → executor
  python seo-agents/agent_checker/agent_checker.py -s "Углекислая ванна" -u http://... -o output/check_uglekislaya.md
  python seo-agents/agent_checker_executor/agent_checker_executor.py -s "Углекислая ванна" -r output/check_uglekislaya.md -o output/tz_uglekislaya.md

  # Из stdin (пайп)
  python agent_checker.py -s "ВЛОК" -u http://... | python agent_checker_executor.py -s "ВЛОК" -o output/tz_vlok.md
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
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent_checker_executor.txt")
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

from api_client import ask_ai  # type: ignore
from logger import get_logger  # type: ignore

logger = get_logger("seo_agents.agent_checker_executor")


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_content(file_path: str | None, stdin: bool = False) -> str:
    if file_path:
        path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if stdin:
        if sys.stdin.isatty():
            print("Вставь отчёт первого агента (Ctrl+Z, Enter — завершить на Windows):", file=sys.stderr)
        return sys.stdin.read()
    return ""


def build_user_message(service_name: str, report: str, page_content: str | None) -> str:
    parts = [
        f"Услуга: **{service_name}**",
        "",
        "Отчёт первого агента (чек-лист):",
        "---",
        report,
        "---",
        "",
        "Сформируй ТЗ для копирайтера и верстальщика по формату из системного промпта.",
    ]
    if page_content:
        parts.extend([
            "",
            "Текущий текст/HTML страницы (для контекста, если нужно указать конкретные места):",
            "---",
            page_content[:8000],  # ограничение
            "---",
        ])
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Агент-исполнитель: по отчёту checker формирует ТЗ для копирайтера и верстальщика"
    )
    parser.add_argument("--service", "-s", required=True, help="Название услуги")
    parser.add_argument("--report", "-r", help="Путь к файлу с отчётом checker")
    parser.add_argument("--page", "-p", help="Путь к файлу с текстом/HTML страницы (опционально)")
    parser.add_argument("--output", "-o", help="Сохранить ТЗ в файл")
    parser.add_argument("--stdin", action="store_true", help="Читать отчёт из stdin (для пайпа)")
    args = parser.parse_args()

    report = load_content(args.report, args.stdin)
    if not report or not report.strip():
        print("Ошибка: отчёт checker пуст. Укажи --report или передай через stdin.", file=sys.stderr)
        sys.exit(1)

    page_content = None
    if args.page:
        try:
            page_content = load_content(args.page, stdin=False)
        except Exception as e:
            print(f"Предупреждение: не удалось прочитать страницу ({e})", file=sys.stderr)

    print("Формирую ТЗ...", file=sys.stderr)
    logger.info("agent_checker_executor: service=%s, report_len=%d", args.service, len(report))

    system_prompt = load_system_prompt()
    user_message = build_user_message(args.service, report, page_content)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tz = ask_ai(messages, max_tokens=3000)
    logger.info("agent_checker_executor: tz length=%d", len(tz))

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(tz)
        print(f"ТЗ сохранено: {out_path}", file=sys.stderr)

    print(tz)


if __name__ == "__main__":
    main()
