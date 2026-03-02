# config_loader.py — общий helper для загрузки shared-config и путей (media, image_protocol)
"""
Единая точка: shared-config.json и CF_IMAGE_STORAGE_ROOT.
Импорт: from config_loader import load_shared_config, get_image_protocol, get_image_storage_root
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Файл в корне content-factory → parent = корень проекта
ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR

_ENV_PATH = PROJECT_ROOT / "config" / ".env"


def load_shared_config() -> dict:
    """Единая точка чтения config/shared-config.json."""
    config_path = PROJECT_ROOT / "config" / "shared-config.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_image_protocol(config: dict | None = None) -> dict:
    """Блок image_protocol из конфига. Если config не передан — загружается заново."""
    if config is None:
        config = load_shared_config()
    return config.get("image_protocol", {})


def get_image_storage_root() -> Path:
    """
    Корень хранилища картинок: CF_IMAGE_STORAGE_ROOT из .env
    или по умолчанию media/ в корне проекта.
    """
    load_dotenv(_ENV_PATH)
    root = os.getenv("CF_IMAGE_STORAGE_ROOT", "").strip()
    if not root:
        return PROJECT_ROOT / "media"
    p = Path(root)
    return p if p.is_absolute() else (PROJECT_ROOT / p)
