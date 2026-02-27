"""
Агент-планировщик контента (Content Planner).
Вход: кластеры ключей / приоритетные услуги, гео, период, лимиты.
Выход: календарь (JSON/CSV) + запись в БД (content_items, content_keywords, agent_tasks).
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Корень content-factory и seo-agents
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEO_AGENTS_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
SHARED_DIR = SEO_AGENTS_DIR / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api_client import ask_ai  # type: ignore

PROMPT_FILE = Path(__file__).resolve().parent / "system_prompt.txt"


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_keywords_context(output_dir: Path) -> str:
    """Собирает последние ключи из output для контекста планировщика."""
    pattern = str(output_dir / "*_keywords_*.txt")
    import glob
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if not files:
        return ""
    text = Path(files[-1]).read_text(encoding="utf-8")
    return text[:2000]


def parse_plan_response(raw: str) -> list[dict]:
    """Извлекает JSON-массив из ответа LLM (возможно в блоке ```json ... ```)."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        raw = match.group(1).strip()
    return json.loads(raw)


def save_plan_to_files(plan: list[dict], output_dir: Path) -> tuple[Path, Path]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"content_plan_{ts}.json"
    csv_path = output_dir / f"content_plan_{ts}.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    # CSV: заголовки + строки
    if plan:
        headers = list(plan[0].keys())
        import csv
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for row in plan:
                row_flat = {}
                for k, v in row.items():
                    row_flat[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
                w.writerow(row_flat)
    return json_path, csv_path


def save_plan_to_db(plan: list[dict]) -> bool:
    """Пишет план в content_items, content_keywords, agent_tasks. Возвращает True, если запись выполнена."""
    try:
        from db import get_connection, is_available
    except ImportError:
        return False
    if not is_available():
        return False
    conn = get_connection()
    written = False
    try:
        cur = conn.cursor()
        channel_blog_id = None
        cur.execute("SELECT id FROM channels WHERE name = 'blog' LIMIT 1")
        row = cur.fetchone()
        if row:
            channel_blog_id = row["id"]
        for i, item in enumerate(plan):
            rubric_key = item.get("rubric_key") or "health_fitness"
            service_key = item.get("service_key") or ""
            cur.execute("SELECT id FROM rubrics WHERE key = %s LIMIT 1", (rubric_key,))
            r = cur.fetchone()
            rubric_id = r["id"] if r else None
            service_id = None
            if service_key:
                cur.execute("SELECT id FROM services WHERE key = %s LIMIT 1", (service_key,))
                s = cur.fetchone()
                service_id = s["id"] if s else None
            planned_date = item.get("period")
            if planned_date and len(planned_date) > 10:
                planned_date = planned_date[:10]
            cur.execute(
                """INSERT INTO content_items
                   (title, description, status, channel_id, rubric_id, service_id, content_type, funnel_stage, planned_date, created_by_agent)
                   VALUES (%s, %s, 'planned', %s, %s, %s, %s, %s, %s, 'planner')
                   RETURNING id""",
                (
                    item.get("title") or "Без названия",
                    item.get("description") or "",
                    channel_blog_id,
                    rubric_id,
                    service_id,
                    item.get("format") or "longread",
                    item.get("funnel_stage") or "awareness",
                    planned_date,
                ),
            )
            row = cur.fetchone()
            content_item_id = row["id"]
            for kw in item.get("keywords") or []:
                if isinstance(kw, str) and kw.strip():
                    cur.execute(
                        """INSERT INTO content_keywords (content_item_id, keyword)
                           VALUES (%s, %s) ON CONFLICT (content_item_id, keyword) DO NOTHING""",
                        (content_item_id, kw.strip()),
                    )
            cur.execute(
                """INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, output_ref, finished_at)
                   VALUES ('planner', %s, 'plan_item', 'done', %s, now())""",
                (content_item_id, json.dumps({"title": item.get("title")})),
            )
        conn.commit()
        written = True
    finally:
        conn.close()
    return written


def main():
    print("=== Агент-планировщик контента ===\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    keywords_ctx = load_keywords_context(OUTPUT_DIR)
    system_prompt = load_system_prompt()
    user_message = (
        "Составь контент-план на ближайшие 2 недели для блога Центра «Энтузиаст».\n"
        "Приоритетные услуги: соляная комната, кедровая фитобочка, массаж, прессотерапия. "
        "Гео: Ноябрьск, Салехард.\n"
        "Лимит: 5–7 материалов. Канал по умолчанию — blog.\n"
    )
    if keywords_ctx:
        user_message += "\nКонтекст по ключевым словам (из последнего файла агента 1):\n" + keywords_ctx[:1500]
    user_message += "\n\nВерни только JSON-массив объектов по формату из системного промпта."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    print("Генерирую план...")
    raw = ask_ai(messages, max_tokens=2500)
    try:
        plan = parse_plan_response(raw)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора JSON: {e}")
        print("Ответ модели (последние 500 символов):", raw[-500:])
        return
    if not plan:
        print("План пуст.")
        return
    json_path, csv_path = save_plan_to_files(plan, OUTPUT_DIR)
    print(f"Календарь сохранён: {json_path.name}, {csv_path.name} ({len(plan)} единиц)")
    if save_plan_to_db(plan):
        print("Данные записаны в БД (content_items, content_keywords, agent_tasks).")
    print("Готово.")


if __name__ == "__main__":
    main()
