# image-agents/shared/image_repository.py — реэкспорт из scripts для обратной совместимости
"""
Единая реализация — scripts/image_repository.py.
Здесь только реэкспорт, чтобы image-agents (store, job_sender) не трогали пути импорта.
"""
import sys
from pathlib import Path

_IMAGE_AGENTS_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.image_repository import (
    load_index,
    save_index,
    add_entry,
    get_images,
    get_hero_image,
    get_index_file_paths,
    set_attachment_id,
)

# Для кода, который вызывал add_image (agent_image_store)
def add_image(post_id: str, image_id: str, file_path: str, purpose: str, wp_attachment_id: int | None = None) -> None:
    add_entry(post_id, image_id, file_path, purpose, wp_attachment_id)
