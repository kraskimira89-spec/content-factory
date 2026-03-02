# image-agents/agent_image_store — следит за готовыми картинками, регистрирует в индексе
"""
Отслеживает появление файлов в output/images/ (по имени post_id_image_id.png),
создаёт записи в db/image_index.json: post_id, image_id, file_path, purpose, created_at.
Опционально: загрузка в WP Media и сохранение wp_attachment_id (заглушка для интеграции).
"""
import json
import sys
from pathlib import Path

# Пути
_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent

if str(PROJECT_ROOT / "seo-agents") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "seo-agents"))
from shared.logger import get_logger  # noqa: E402

# Локальный shared image-agents
if str(_IMAGE_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_IMAGE_AGENTS_DIR))
from shared.image_repository import add_image, get_index_file_paths  # noqa: E402

logger = get_logger("image_agents.store")

_CONFIG_PATH = PROJECT_ROOT / "config" / "shared-config.json"
_CONFIG = json.loads(_CONFIG_PATH.read_text("utf-8")) if _CONFIG_PATH.exists() else {}
_IMG = _CONFIG.get("image_agents", {})
STORAGE_DIR = PROJECT_ROOT / _IMG.get("image_storage_path", "output/images")
JOBS_DIR = PROJECT_ROOT / _IMG.get("image_jobs_path", "output/image_jobs")


def purpose_from_image_id(image_id: str) -> str:
    """По image_id подставляем purpose (hero, step_1 и т.д.)."""
    if image_id == "hero":
        return "hero"
    if image_id.startswith("step_"):
        return "step"
    return "illustration"


def discover_new_images() -> list[tuple[Path, str, str]]:
    """
    Сканирует STORAGE_DIR, находит файлы вида {post_id}-{image_id}.png (дефис).
    Возвращает список (path, post_id, image_id).
    """
    if not STORAGE_DIR.exists():
        return []
    seen = get_index_file_paths()
    result = []
    for path in STORAGE_DIR.iterdir():
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        # file_path в индексе — относительный, например output/images/123-hero.png
        try:
            rel_path = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = path
        rel_str = str(rel_path).replace("\\", "/")
        if rel_str in seen:
            continue
        stem = path.stem  # post_id-image_id
        if "-" in stem:
            parts = stem.split("-", 1)  # post_id, image_id (image_id может содержать -)
            if len(parts) >= 2:
                post_id, image_id = parts[0], parts[1]
                result.append((path, post_id, image_id))
    return result


def run(upload_to_wp: bool = False) -> int:
    """
    Сканирует output/images/, для каждого нового файла добавляет запись в индекс.
    upload_to_wp: если True — вызвать загрузку в WP и сохранить wp_attachment_id (заглушка).
    Возвращает количество добавленных записей.
    """
    added = 0
    for path, post_id, image_id in discover_new_images():
        purpose = purpose_from_image_id(image_id)
        wp_id = None
        if upload_to_wp:
            # Заглушка: здесь можно вызвать WP Media API и получить attachment ID
            pass
        try:
            file_path_rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            file_path_rel = path
        file_path_str = str(file_path_rel).replace("\\", "/")
        add_image(post_id, image_id, file_path_str, purpose, wp_attachment_id=wp_id)
        logger.info("Зарегистрирована картинка: %s -> %s", path.name, post_id)
        added += 1
    return added


if __name__ == "__main__":
    n = run(upload_to_wp=False)
    print(f"Добавлено в индекс: {n}")
