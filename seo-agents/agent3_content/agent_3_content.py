import os
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Пути
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent3_content.txt")
KONFERENC_ZAL_PROMPT = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent3_konferenc_zal.txt")

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from api_client import ask_ai  # type: ignore
from keywords_db import load_keywords  # type: ignore
from db_session import get_last_pair  # type: ignore
from logger import get_logger  # type: ignore
from prompt_loader import load_brand_voice  # type: ignore

console = Console()
logger = get_logger("seo_agents.agent3")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def load_system_prompt(prompt_file: str | None = None) -> str:
    """Системный промпт + общий brand voice из prompts/context/."""
    path = prompt_file or PROMPT_FILE
    with open(path, "r", encoding="utf-8") as f:
        base_prompt = f.read()
    try:
        brand = load_brand_voice()
        return f"{base_prompt}\n\n--- ОБЩИЙ КОНТЕКСТ БРЕНДА ---\n{brand}"
    except FileNotFoundError:
        return base_prompt


def load_last_brief(service_name: str, city: str) -> str | None:
    """Ищем последний бриф в output для этой услуги и города."""
    safe_service = service_name.replace(" ", "_")
    safe_city = city.replace(" ", "_")
    pattern = f"brief_{safe_service}_{safe_city}.md"

    files = [
        f for f in os.listdir(OUTPUT_DIR)
        if f.endswith(pattern)
    ]
    if not files:
        return None
    # берём самый свежий
    files.sort(reverse=True)
    filepath = os.path.join(OUTPUT_DIR, files[0])
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def generate_page_text(
    service_name: str,
    city: str,
    keywords_text: str,
    brief_text: str,
    system_prompt: str
) -> str:
    user_message = (
        f"Напиши текст страницы услуги для сайта Центра «Энтузиаст».\n\n"
        f"Услуга: {service_name}\n"
        f"Город: {city}\n\n"
        f"Ключевые фразы для SEO (вписывай органично):\n{keywords_text}\n\n"
        f"ТЗ и структура страницы (бриф от Агента 2):\n{brief_text}\n\n"
        f"Соблюдай структуру и стиль из системного промпта. "
        f"Выдай готовый текст в формате Markdown."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    return ask_ai(messages, max_tokens=2500)


def save_page(service_name: str, city: str, page_text: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_service = service_name.replace(" ", "_")
    safe_city = city.replace(" ", "_")

    filename = f"{timestamp}_page_{safe_service}_{safe_city}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(page_text)

    return filepath


def fetch_one_planned_item():
    """
    Берёт одну контент-единицу со статусом planned из БД.
    Возвращает dict с id, title, description, rubric_key, content_type, keywords (список), service_name
    или None, если БД недоступна или записей нет.
    """
    try:
        from db import get_connection, is_available
    except ImportError:
        return None
    if not is_available():
        return None
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT ci.id, ci.title, ci.description, ci.content_type, r.key AS rubric_key, s.name AS service_name
               FROM content_items ci
               LEFT JOIN rubrics r ON r.id = ci.rubric_id
               LEFT JOIN services s ON s.id = ci.service_id
               WHERE ci.status = 'planned'
               ORDER BY ci.planned_date NULLS FIRST, ci.id
               LIMIT 1"""
        )
        row = cur.fetchone()
        if not row:
            return None
        item_id = row["id"]
        cur.execute("SELECT keyword FROM content_keywords WHERE content_item_id = %s", (item_id,))
        keywords = [r["keyword"] for r in cur.fetchall()]
        return {
            "id": item_id,
            "title": row["title"] or "",
            "description": row["description"] or "",
            "content_type": row["content_type"] or "longread",
            "rubric_key": row["rubric_key"] or "health_fitness",
            "service_name": row["service_name"] or row["title"] or "Услуга",
            "keywords": keywords,
        }
    finally:
        conn.close()


def save_page_for_db(item: dict, page_text: str) -> str:
    """Сохраняет .md и .meta.json для задачи из БД, обновляет content_versions и status."""
    import json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = (item.get("title") or "page").replace(" ", "_")[:50]
    filename = f"{timestamp}_page_{safe_title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(page_text)
    meta = {
        "rubric_key": item.get("rubric_key"),
        "content_type": item.get("content_type"),
        "content_item_id": item["id"],
    }
    meta_path = filepath + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    try:
        from db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 AS v FROM content_versions WHERE content_item_id = %s",
            (item["id"],),
        )
        ver = cur.fetchone()["v"]
        cur.execute(
            """INSERT INTO content_versions (content_item_id, version, source_agent, text, meta)
               VALUES (%s, %s, 'writer', %s, %s)""",
            (item["id"], ver, page_text, json.dumps({"file": filename})),
        )
        cur.execute("UPDATE content_items SET status = 'draft_ready', updated_at = now() WHERE id = %s", (item["id"],))
        cur.execute(
            """INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, output_ref, finished_at)
               VALUES ('writer', %s, 'write_draft', 'done', %s, now())""",
            (item["id"], json.dumps({"version": ver, "file": filename})),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return filepath


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Агент 3 — генератор текста страницы")
    parser.add_argument("--konferenc-zal", action="store_true", help="Использовать промпт для конференц-зала")
    args = parser.parse_args()

    console.print("\n[bold cyan]Агент 3 — генератор текста страницы[/bold cyan]\n")

    prompt_file = KONFERENC_ZAL_PROMPT if args.konferenc_zal else None

    # Режим БД: одна задача из контент-плана (status=planned)
    item = fetch_one_planned_item()
    if item:
        logger.info("Режим БД: контент-единица id=%s", item["id"])
        console.print(f"Задача из плана: [green]{item['title']}[/green] (рубрика: {item['rubric_key']})\n")
        keywords_text = "\n".join(item["keywords"]) if item["keywords"] else ""
        brief_text = (item["description"] or "") + ("\n\nКлючевые слова: " + ", ".join(item["keywords"]) if item["keywords"] else "")
        service_name = item["service_name"]
        city = "Ноябрьск"
        console.print("[dim]Читаю системный промпт...[/dim]")
        system_prompt = load_system_prompt(prompt_file)
        console.print("[dim]Генерирую текст страницы... подожди 20-40 секунд...[/dim]\n")
        page_text = generate_page_text(service_name, city, keywords_text, brief_text, system_prompt)
        logger.info("Текст сгенерирован по задаче БД id=%s, length=%d", item["id"], len(page_text or ""))
        console.print(Panel(
            page_text[:1500] + "\n\n[dim]...полный текст в файле...[/dim]",
            title="[bold green]Черновик страницы (начало)[/bold green]",
            border_style="green"
        ))
        filepath = save_page_for_db(item, page_text)
        console.print("\n[bold green]Готово![/bold green]")
        console.print(f"Файл сохранён: [yellow]{filepath}[/yellow]")
        console.print("[dim]Метаданные (.meta.json) записаны для Агента 4.[/dim]\n")
        return

    # Режим файлов: последняя пара услуга+город из db_session
    last = get_last_pair()
    if not last:
        logger.info("Нет данных о последней услуге в БД")
        console.print(
            "[red]Нет данных о последней услуге.[/red]\n"
            "Сначала запусти Агента 1 (или запланируй задачу через Агента-планировщика).\n"
        )
        return

    service_name, city = last
    logger.info("Старт генерации страницы: service=%s, city=%s", service_name, city)
    console.print(
        f"Использую: [green]{service_name} — {city}[/green]\n"
    )

    keywords_text = load_keywords(service_name, city)
    if not keywords_text:
        logger.info(
            "Нет ключей в БД для генерации страницы: service=%s, city=%s",
            service_name,
            city,
        )
        console.print(
            "[red]Нет ключей в базе. Запусти Агента 1.[/red]\n"
        )
        return

    brief_text = load_last_brief(service_name, city)
    if not brief_text:
        logger.info(
            "Нет брифа в output для генерации страницы: service=%s, city=%s",
            service_name,
            city,
        )
        console.print(
            "[red]Нет брифа в output. Запусти Агента 2.[/red]\n"
        )
        return

    console.print("[dim]Читаю системный промпт...[/dim]")
    system_prompt = load_system_prompt(prompt_file)

    console.print("[dim]Генерирую текст страницы... подожди 20-40 секунд...[/dim]\n")

    page_text = generate_page_text(
        service_name, city, keywords_text, brief_text, system_prompt
    )
    logger.info(
        "Текст страницы сгенерирован: service=%s, city=%s, length=%d",
        service_name,
        city,
        len(page_text or ""),
    )

    console.print(Panel(
        page_text[:1500] + "\n\n[dim]...полный текст в файле...[/dim]",
        title="[bold green]Черновик страницы (начало)[/bold green]",
        border_style="green"
    ))

    filepath = save_page(service_name, city, page_text)
    logger.info("Страница сохранена в файл: %s", filepath)

    console.print("\n[bold green]Готово![/bold green]")
    console.print(f"Файл сохранён: [yellow]{filepath}[/yellow]\n")


if __name__ == "__main__":
    main()
