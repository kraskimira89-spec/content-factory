"""
Заполняет Google Sheets (Services, Topics, Queue) данными из проекта.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / "config" / ".env")

from scripts.sheets_client import read_queue, write_sheet_range

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1uL2BUXrN-E85s3OEz9DjzeT8rQouBpTQZOMjwUEmquo")

# Известные wp_page_id из очереди (можно дополнить из output/last_publish.json)
WP_KNOWN = {
    "aromaterapiya": ("2899", "http://91.229.11.147/uslugi/aromaterapiya/"),
    "massazh": ("162", "http://91.229.11.147/uslugi/massazh/"),
}
WP_URL_BASE = os.getenv("WP_URL", "http://91.229.11.147").rstrip("/")


def load_services() -> list[dict]:
    """Объединяет services.json + uslugi. Приоритет: uslugi (ароматерапия, гидромассаж...) сначала."""
    svc_path = PROJECT_ROOT / "prompts" / "context" / "services.json"
    svc_list = json.loads(svc_path.read_text(encoding="utf-8")) if svc_path.is_file() else []

    cfg = json.loads((PROJECT_ROOT / "config" / "shared-config.json").read_text(encoding="utf-8"))
    uslugi = cfg.get("uslugi", {})

    by_slug = {s["slug"]: dict(s) for s in svc_list}
    for slug, data in uslugi.items():
        if slug not in by_slug:
            by_slug[slug] = {"slug": slug, "name": data.get("name", slug), "category": "Услуги", "price_from": None}
        else:
            by_slug[slug]["name"] = data.get("name", by_slug[slug]["name"])

    # Порядок: сначала uslugi (приоритетные услуги), затем остальные из services.json
    order = list(uslugi.keys()) + [s["slug"] for s in svc_list if s["slug"] not in uslugi]
    return [by_slug[s] for s in order if s in by_slug]


def fill_services(spreadsheet_id: str) -> None:
    """Заполняет лист Services."""
    services = load_services()
    wp_known = dict(WP_KNOWN)
    rows = [["slug", "wp_page_id", "category", "price", "wp_url", "name"]]
    for s in services:
        slug = s.get("slug", "")
        wp = wp_known.get(slug, ("-", "-"))
        wp_id, wp_url = wp[0], wp[1]
        if wp_url == "-" and wp_id != "-":
            wp_url = f"{WP_URL_BASE}/uslugi/{slug}/"
        price = s.get("price_from")
        price_str = str(price) if price is not None else ""
        rows.append([
            slug,
            wp_id,
            s.get("category", ""),
            price_str,
            wp_url,
            s.get("name", ""),
        ])
    write_sheet_range(spreadsheet_id, "Services!A1:F" + str(len(rows)), rows)
    print(f"Services: записано {len(rows) - 1} строк")


def fill_topics(spreadsheet_id: str) -> None:
    """Заполняет лист Topics (topic_id, service_slug, target_keyword, status)."""
    services = load_services()
    headers = ["topic_id", "service_slug", "target_keyword", "status"]
    rows = [headers]
    for i, s in enumerate(services[:10], start=1):
        slug = s.get("slug", "")
        name = s.get("name", slug)
        topic_id = f"T{i:03d}"
        target_kw = f"{name} Ноябрьск"
        rows.append([topic_id, slug, target_kw, "active"])
    if len(rows) <= 1:
        return
    write_sheet_range(spreadsheet_id, "Topics!A1:D" + str(len(rows)), rows)
    print(f"Topics: записано {len(rows) - 1} строк")


def fill_queue(spreadsheet_id: str) -> None:
    """Заполняет лист Queue — Services с wp_page_id=done, остальные queue."""
    services = load_services()
    wp_known = dict(WP_KNOWN)
    headers = ["queue_id", "topic_id", "service_slug", "publish_date", "status", "wp_page_id", "wp_url", "agent_run_id", "notes"]
    rows = [headers]
    dates = ["2026-03-04", "2026-03-10", "2026-03-17", "2026-03-24", "2026-03-31", "2026-04-07"]
    for i, s in enumerate(services[:8]):
        slug = s.get("slug", "")
        wp = wp_known.get(slug, ("-", "-"))
        status = "done" if wp[0] != "-" else "queue"
        wp_url = wp[1] if wp[1] != "-" else f"{WP_URL_BASE}/uslugi/{slug}/"
        notes = "Опубликовано" if status == "done" else ("Следующая на генерацию" if i < 3 else "")
        if status == "queue" and i == 1:
            notes = "Следующая на генерацию"
        rows.append([
            f"Q{i+1:03d}",
            f"T{i+1:03d}",
            slug,
            dates[i] if i < len(dates) else "",
            status,
            wp[0],
            wp_url if status == "done" else "-",
            "-",
            notes,
        ])
    write_sheet_range(spreadsheet_id, "Queue!A1:I" + str(len(rows)), rows)
    print(f"Queue: записано {len(rows) - 1} строк")


def main():
    print("Заполнение Google Sheets...")
    print(f"Spreadsheet ID: {SHEET_ID}\n")

    fill_services(SHEET_ID)
    fill_topics(SHEET_ID)
    fill_queue(SHEET_ID)

    print("\nГотово.")


if __name__ == "__main__":
    main()
