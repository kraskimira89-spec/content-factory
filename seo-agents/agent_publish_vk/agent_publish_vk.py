# Publisher ВК: публикация анонса в группу (wall.post) и запись в publishing_log
import os
import sys
import json
from pathlib import Path

import requests

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / "config" / ".env")

VK_API_VERSION = "5.131"


def load_vk_env():
    """VK_ACCESS_TOKEN, VK_GROUP_ID (числовой ID группы, без минуса)."""
    token = os.getenv("VK_ACCESS_TOKEN", "").strip()
    group_id = os.getenv("VK_GROUP_ID", "").strip()
    if not token or not group_id or not group_id.lstrip("-").isdigit():
        raise RuntimeError("В .env задайте VK_ACCESS_TOKEN и VK_GROUP_ID (число).")
    return token, int(group_id) if int(group_id) > 0 else int(group_id)


def fetch_one_published_to_wp_not_vk():
    """
    Один content_item: уже есть запись в publishing_log с platform=wordpress,
    нет записи с platform=vk. Возвращает id, title, wp_url или None.
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
            SELECT ci.id, ci.title, pl_wp.url AS wp_url
            FROM content_items ci
            JOIN publishing_log pl_wp ON pl_wp.content_item_id = ci.id
                AND pl_wp.platform = 'wordpress' AND pl_wp.status = 'success'
            WHERE ci.status = 'published'
              AND NOT EXISTS (
                  SELECT 1 FROM publishing_log pl2
                  WHERE pl2.content_item_id = ci.id AND pl2.platform = 'vk'
              )
            ORDER BY pl_wp.published_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row["id"], "title": row["title"] or "", "wp_url": row["wp_url"] or ""}
    finally:
        conn.close()


def get_channel_id_vk():
    """ID канала vk в таблице channels."""
    try:
        from db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM channels WHERE name = 'vk' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row["id"] if row else None
    except Exception:
        return None


def vk_wall_post(access_token: str, group_id: int, message: str) -> dict:
    """
    Публикует пост на стену сообщества. owner_id = -group_id.
    Возвращает ответ API (post_id в response).
    """
    url = "https://api.vk.com/method/wall.post"
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "owner_id": -abs(group_id),
        "message": message,
        "from_group": 1,
    }
    resp = requests.post(url, params=params, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"VK API error: {data['error'].get('error_msg', data)}")
    return data.get("response", {})


def save_publishing_log_and_task(content_item_id: int, channel_id: int, owner_id: int, post_id: int, response_raw: dict):
    vk_url = f"https://vk.com/wall{owner_id}_{post_id}"
    external_id = f"{owner_id}_{post_id}"
    try:
        from db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO publishing_log
               (content_item_id, channel_id, platform, external_id, url, published_at, status, response_raw)
               VALUES (%s, %s, 'vk', %s, %s, now(), 'success', %s)""",
            (content_item_id, channel_id, external_id, vk_url, json.dumps(response_raw)),
        )
        cur.execute(
            """INSERT INTO agent_tasks (agent_name, content_item_id, task_type, status, input_ref, output_ref, finished_at)
               VALUES ('publisher', %s, 'publish_vk', 'done', %s, %s, now())""",
            (
                content_item_id,
                '{"target_platform": "vk"}',
                json.dumps({"owner_id": owner_id, "post_id": post_id, "url": vk_url}),
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        raise


def main():
    print("=== Publisher ВК: анонс в группу (wall.post) ===\n")

    try:
        access_token, group_id = load_vk_env()
    except RuntimeError as e:
        print(f"Настройка: {e}")
        return

    item = fetch_one_published_to_wp_not_vk()
    if not item:
        print("Нет материалов, опубликованных в WordPress и ещё не в ВК.")
        return

    content_item_id = item["id"]
    title = item["title"]
    wp_url = item["wp_url"]
    message = f"{title}\n\nЧитать на сайте: {wp_url}" if wp_url else title

    print(f"Материал: {title} (id={content_item_id})")
    print("Публикую в ВК...")

    try:
        response = vk_wall_post(access_token, group_id, message)
        post_id = response.get("post_id")
        if post_id is None:
            print("Ошибка: в ответе VK нет post_id.")
            return
        owner_id = -abs(group_id)
        save_publishing_log_and_task(
            content_item_id,
            get_channel_id_vk() or 2,
            owner_id,
            post_id,
            {"owner_id": owner_id, "post_id": post_id},
        )
        vk_url = f"https://vk.com/wall{owner_id}_{post_id}"
        print(f"Опубликовано: {vk_url}")
    except Exception as e:
        print(f"Ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
