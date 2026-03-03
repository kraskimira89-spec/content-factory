"""
Агент-исполнитель на сайте: по ТЗ от второго агента формирует конкретные правки в теме/админке.

Вход:
  - Название услуги и/или URL (/uslugi/uglekislaya-vanna/)
  - ТЗ от agent_checker_executor (файл или stdin)

Выход:
  - Список изменений по файлам темы
  - Действия в админке/API
  - Проверка: какие блоки эталона закрыты

Использование:
  python seo-agents/agent_checker_implementer/agent_checker_implementer.py -s "Углекислая ванна" -t output/tz_uglekislaya.md -o output/impl_uglekislaya.md
  python seo-agents/agent_checker_implementer/agent_checker_implementer.py -u /uslugi/vlok/ -t output/tz_vlok.md
"""

import argparse
import json
import os
import re
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent_checker_implementer.txt")
CONTEXT_FILE = os.path.join(PROJECT_ROOT, "prompts", "context", "theme-service-structure.md")
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "shared-config.json")

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

from api_client import ask_ai  # type: ignore
from logger import get_logger  # type: ignore

logger = get_logger("seo_agents.agent_checker_implementer")


def load_system_prompt() -> str:
    base = open(PROMPT_FILE, "r", encoding="utf-8").read().strip()
    if os.path.isfile(CONTEXT_FILE):
        ctx = open(CONTEXT_FILE, "r", encoding="utf-8").read()
        base += "\n\n--- КОНТЕКСТ СТРУКТУРЫ ТЕМЫ ---\n" + ctx
    return base


def slug_from_url(url: str) -> str | None:
    """Извлекает slug из URL /uslugi/uglekislaya-vanna/ или /uslugi/uglekislaya-vanna."""
    m = re.search(r"/uslugi/([a-z0-9\-]+)/?", url)
    return m.group(1) if m else None


def slug_from_service_name(service_name: str) -> str | None:
    """Сопоставляет название услуги со slug из shared-config.json."""
    if not os.path.isfile(CONFIG_FILE):
        return None
    cfg = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))
    name_lower = service_name.strip().lower()
    for src in (cfg.get("services", {}), cfg.get("uslugi", {})):
        for slug, data in src.items():
            if data.get("name", "").lower() == name_lower:
                return slug
            for alias in data.get("aliases", []):
                if alias.lower() == name_lower:
                    return slug
    return None


def load_content(file_path: str | None, stdin: bool = False) -> str:
    if file_path:
        path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if stdin:
        if sys.stdin.isatty():
            print("Вставь ТЗ от второго агента (Ctrl+Z, Enter — завершить):", file=sys.stderr)
        return sys.stdin.read()
    return ""


def build_user_message(service_name: str | None, slug: str | None, url: str | None, tz_content: str) -> str:
    parts = []
    if service_name:
        parts.append(f"Услуга: **{service_name}**")
    if slug:
        parts.append(f"Slug: `{slug}`")
    if url:
        parts.append(f"URL: {url}")
    if not parts:
        parts.append("Услуга не указана — определи по контексту ТЗ.")
    parts.extend(["", "ТЗ от второго агента:", "---", tz_content, "---", "", "Сформируй список изменений по файлам темы и действиям в админке."])
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Агент-исполнитель: по ТЗ формирует правки в теме и админке"
    )
    parser.add_argument("--service", "-s", help="Название услуги")
    parser.add_argument("--url", "-u", help="URL страницы (/uslugi/uglekislaya-vanna/ или полный)")
    parser.add_argument("--slug", help="Slug услуги напрямую (uglekislaya-vanna)")
    parser.add_argument("--tz", "-t", help="Путь к файлу с ТЗ от executor")
    parser.add_argument("--output", "-o", help="Сохранить результат в файл")
    parser.add_argument("--stdin", action="store_true", help="Читать ТЗ из stdin")
    args = parser.parse_args()

    slug = args.slug or (slug_from_url(args.url or "") if args.url else None)
    if not slug and args.service:
        slug = slug_from_service_name(args.service)
    if not slug and args.url:
        slug = slug_from_url(args.url)

    tz_content = load_content(args.tz, args.stdin)
    if not tz_content or not tz_content.strip():
        print("Ошибка: ТЗ пусто. Укажи --tz или передай через stdin.", file=sys.stderr)
        sys.exit(1)

    print("Формирую список изменений...", file=sys.stderr)
    logger.info("agent_checker_implementer: service=%s, slug=%s, tz_len=%d", args.service, slug, len(tz_content))

    system_prompt = load_system_prompt()
    user_message = build_user_message(args.service, slug, args.url, tz_content)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    result = ask_ai(messages, max_tokens=3500)
    logger.info("agent_checker_implementer: result length=%d", len(result))

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Результат сохранён: {out_path}", file=sys.stderr)

    print(result)


if __name__ == "__main__":
    main()
