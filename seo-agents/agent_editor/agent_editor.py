# Агент Editor: берёт черновики (draft_ready), правит текст, утверждает (approved)
import os
import sys
import json

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_client import ask_ai  # type: ignore
from logger import get_logger  # type: ignore

logger = get_logger("seo_agents.agent_editor")
PROMPT_FILE = os.path.join(PROJECT_ROOT, "prompts", "agents", "agent_editor.txt")


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def fetch_one_draft_ready():
    """
    Один материал со статусом draft_ready и последней версией текста.
    Возвращает dict: id, title, description, version, version_id, text, meta, rubric_key или None.
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
            """
            SELECT ci.id, ci.title, ci.description, r.key AS rubric_key,
                   cv.id AS version_id, cv.version, cv.text, cv.meta
            FROM content_items ci
            LEFT JOIN rubrics r ON r.id = ci.rubric_id
            JOIN LATERAL (
                SELECT id, version, text, meta
                FROM content_versions v
                WHERE v.content_item_id = ci.id
                ORDER BY v.version DESC
                LIMIT 1
            ) AS cv ON true
            WHERE ci.status = 'draft_ready'
            ORDER BY ci.planned_date NULLS FIRST, ci.priority DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        meta = row["meta"]
        if isinstance(meta, dict):
            pass
        elif isinstance(meta, str):
            try:
                meta = json.loads(meta) if meta else {}
            except Exception:
                meta = {}
        else:
            meta = {}
        return {
            "id": row["id"],
            "title": row["title"] or "",
            "description": row["description"] or "",
            "rubric_key": row["rubric_key"] or "health_fitness",
            "version_id": row["version_id"],
            "version": row["version"],
            "text": row["text"] or "",
            "meta": meta,
        }
    finally:
        conn.close()


def edit_text_with_llm(title: str, description: str, text: str, system_prompt: str) -> str:
    """Отдаёт текст в LLM для правки, возвращает отредактированный Markdown."""
    user_message = (
        f"Заголовок материала: {title}\n\n"
        f"Описание/ТЗ: {description}\n\n"
        f"Черновик текста (отредактируй по правилам из системного промпта):\n\n{text}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return ask_ai(messages, max_tokens=4000)


def save_approved_version(
    content_item_id: int,
    last_writer_version: int,
    edited_text: str,
    meta: dict,
    rubric_key: str = "health_fitness",
):
    """
    Сохраняет новую версию от editor, ставит status=approved, пишет в agent_tasks.
    Дополнительно пишет утверждённый текст в output/*.md для публикации Агентом 4.
    """
    from db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        new_version = last_writer_version + 1
        cur.execute(
            """INSERT INTO content_versions (content_item_id, version, source_agent, text, meta)
               VALUES (%s, %s, 'editor', %s, %s)""",
            (content_item_id, new_version, edited_text, json.dumps(meta)),
        )
        cur.execute(
            "UPDATE content_items SET status = 'approved', updated_at = now() WHERE id = %s",
            (content_item_id,),
        )
        cur.execute(
            """INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
               VALUES ('editor', %s, 'edit', 'done', %s, %s, now())""",
            (
                content_item_id,
                json.dumps({"last_writer_version": last_writer_version}),
                json.dumps({"approved_version": new_version}),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Файл в output, чтобы Агент 4 опубликовал утверждённую версию (последний по mtime)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = (meta.get("title") or "page")[:50].replace(" ", "_")
    filename = f"{ts}_page_approved_{content_item_id}_{safe_title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(edited_text)
    meta_path = filepath + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as m:
        json.dump(
            {"content_item_id": content_item_id, "rubric_key": rubric_key},
            m,
            ensure_ascii=False,
        )
    logger.info("Editor: записан файл для публикации %s", filepath)


def main():
    print("=== Агент Editor: черновик → правки → утверждение ===\n")

    item = fetch_one_draft_ready()
    if not item:
        print("Нет материалов со статусом draft_ready или БД недоступна.")
        logger.info("Editor: нет draft_ready")
        return

    content_item_id = item["id"]
    print(f"Материал: {item['title']} (id={content_item_id}, версия Writer: {item['version']})")

    system_prompt = load_system_prompt()
    print("Редактирую текст (LLM)...")
    edited = edit_text_with_llm(
        item["title"],
        item["description"],
        item["text"],
        system_prompt,
    )
    if not edited or not edited.strip():
        print("Ошибка: пустой ответ от редактора.")
        return

    meta = dict(item.get("meta") or {})
    meta["medical_compliance_checked"] = True
    meta["language"] = "ru"
    meta["title"] = item["title"]

    save_approved_version(
        content_item_id,
        item["version"],
        edited.strip(),
        meta,
        item.get("rubric_key") or "health_fitness",
    )
    print(f"Готово: сохранена версия {item['version'] + 1}, статус = approved.")
    logger.info("Editor: approved content_item_id=%s version=%s", content_item_id, item["version"] + 1)


if __name__ == "__main__":
    main()
