import json
import os
from datetime import datetime

# Базовые пути (можно позже брать из shared-config.json)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # корень проекта (там, где content-factory)
DB_PATH = os.path.join(BASE_DIR, "db", "image_index.json")


def _ensure_index_file():
    """Гарантирует, что db/image_index.json существует и в нём хотя бы {}."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            f.write("{}")


def load_index():
    """Читает весь индекс в виде dict: {post_id: [images...]}."""
    _ensure_index_file()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # если файл побился — начинаем с пустого объекта
            data = {}
    # гарантируем, что ключи — строки
    if not isinstance(data, dict):
        data = {}
    return data


def save_index(index_dict):
    """Сохраняет индекс обратно в JSON (красиво отформатированный)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(index_dict, f, ensure_ascii=False, indent=2)


def add_entry(post_id, image_id, file_path, purpose, wp_attachment_id=None, created_at=None):
    """
    Добавляет запись о картинке в индекс.
    post_id: str|int   – ID поста (будет приведён к строке)
    image_id: str      – логический id картинки (hero, step_1 и т.п.)
    file_path: str     – путь к файлу (от корня проекта или абсолютный)
    purpose: str       – назначение (hero, step, gallery и т.п.)
    wp_attachment_id: int|None – ID вложения в WordPress (если уже загружена)
    created_at: str|None – ISO-время; если None, ставим текущее
    """
    index = load_index()
    key = str(post_id)

    if created_at is None:
        created_at = datetime.utcnow().isoformat(timespec="seconds")

    entry = {
        "image_id": image_id,
        "file_path": file_path,
        "purpose": purpose,
        "wp_attachment_id": wp_attachment_id,
        "created_at": created_at,
    }

    if key not in index or not isinstance(index[key], list):
        index[key] = []

    # можно убрать дубликаты по image_id
    index[key] = [e for e in index[key] if e.get("image_id") != image_id]
    index[key].append(entry)

    save_index(index)


def get_images(post_id):
    """
    Возвращает список всех картинок для post_id.
    Если нет записей — возвращает пустой список.
    """
    index = load_index()
    return index.get(str(post_id), [])


def get_hero_image(post_id):
    """
    Возвращает первую картинку с purpose == 'hero' для post_id.
    Если нет, пытается вернуть первую картинку вообще.
    Если ничего нет — возвращает None.
    """
    images = get_images(post_id)
    if not images:
        return None

    # сначала ищем hero
    for img in images:
        if img.get("purpose") == "hero":
            return img

    # иначе возвращаем первую
    return images[0]


def get_index_file_paths():
    """Множество всех зарегистрированных file_path (для agent_image_store)."""
    index = load_index()
    out = set()
    for records in index.values():
        for r in records:
            if r.get("file_path"):
                out.add(r["file_path"])
    return out


def set_attachment_id(post_id, image_id, wp_attachment_id):
    """Обновляет wp_attachment_id в записи индекса после загрузки в WP Media."""
    index = load_index()
    key = str(post_id)
    if key not in index:
        return
    for rec in index[key]:
        if rec.get("image_id") == image_id:
            rec["wp_attachment_id"] = wp_attachment_id
            break
    save_index(index)
