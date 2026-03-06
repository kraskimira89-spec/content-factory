"""
Оркестратор: читает Queue из Google Sheets, запускает цепочку агентов.
"""
import os
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "seo-agents" / "shared"))

load_dotenv(PROJECT_ROOT / "config" / ".env")

from scripts.sheets_client import read_queue, update_queue_row

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1uL2BUXrN-E85s3OEz9DjzeT8rQouBpTQZOMjwUEmquo")

COL_STATUS = "E"
COL_WP_PAGE_ID = "F"
COL_WP_URL = "G"
COL_AGENT_RUN = "H"


def get_service_name_by_slug(slug: str) -> str | None:
    """Название услуги по slug из shared или config."""
    from prompt_loader import get_service_name_by_slug as _get  # type: ignore
    return _get(slug)


def find_next_row(rows: list[dict]) -> tuple[dict, int] | None:
    """Берёт первую строку queue по publish_date. Возвращает (task, sheet_row_number)."""
    sorted_rows = sorted(rows, key=lambda r: r.get("publish_date") or r.get("planned_date") or "9999")
    if not sorted_rows:
        return None
    task = sorted_rows[0]
    all_rows = read_queue(SHEET_ID, status_filter=None)
    for i, r in enumerate(all_rows):
        if (r.get("queue_id") or r.get("id")) == (task.get("queue_id") or task.get("id")):
            return task, i + 2  # строка 1 — заголовок
    return None


def run_agents(slug: str) -> dict:
    """Запускает цепочку agent1 → agent2 → agent3 → agent4 для slug."""
    service_name = get_service_name_by_slug(slug)
    if not service_name:
        print(f"[!] Услуга со slug «{slug}» не найдена.")
        return {"success": False, "agent": "resolve"}

    py = sys.executable
    agents = [
        [py, "seo-agents/agent1_keywords/agent_1_keywords.py", "-s", service_name],
        [py, "seo-agents/agent2_brief/agent_2_brief.py", "-s", service_name],
        [py, "seo-agents/agent3_content/agent_3_content.py"],
        [py, "seo-agents/agent4_publish/agent_4_publish.py", slug],
    ]
    for cmd in agents:
        print(f"\n>> Запуск: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), shell=False)
        if result.returncode != 0:
            print(f"[!] Ошибка при выполнении {cmd[1]}, returncode={result.returncode}")
            return {"success": False, "agent": cmd[1]}
    return {"success": True}


def get_wp_result(slug: str) -> dict:
    """Читает wp_page_id и wp_url из output/last_publish.json."""
    path = PROJECT_ROOT / "output" / "last_publish.json"
    if path.is_file():
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("slug") == slug:
            return {
                "wp_page_id": str(data.get("wp_page_id", "-")),
                "wp_url": data.get("wp_url", "-"),
            }
    return {"wp_page_id": "-", "wp_url": "-"}


def main():
    print(f"\n{'='*50}")
    print(f"[run_from_queue] Старт: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    rows = read_queue(SHEET_ID, "queue")
    if not rows:
        print("Очередь пуста — нечего запускать.")
        return

    result_pair = find_next_row(rows)
    if not result_pair:
        print("Не удалось определить строку для запуска.")
        return

    task, row_number = result_pair
    slug = (task.get("service_slug") or task.get("slug") or "").strip()
    queue_id = task.get("queue_id") or task.get("id") or ""

    if not slug:
        print("В задаче не указан service_slug.")
        return

    print(f"Берём задачу: {queue_id} | slug={slug} | строка={row_number}")

    # Ставим статус in_progress
    update_queue_row(SHEET_ID, row_number, {
        COL_STATUS: "in_progress",
        COL_AGENT_RUN: datetime.now().strftime("%Y%m%d_%H%M%S"),
    })

    # Запускаем агентов
    run_result = run_agents(slug)

    if run_result["success"]:
        wp = get_wp_result(slug)
        update_queue_row(SHEET_ID, row_number, {
            COL_STATUS: "done",
            COL_WP_PAGE_ID: wp["wp_page_id"],
            COL_WP_URL: wp["wp_url"],
        })
        print(f"\n[OK] Готово! wp_page_id={wp['wp_page_id']} url={wp['wp_url']}")
    else:
        update_queue_row(SHEET_ID, row_number, {
            COL_STATUS: "error",
        })
        print(f"\n[!] Ошибка при агенте: {run_result['agent']}")


if __name__ == "__main__":
    main()
