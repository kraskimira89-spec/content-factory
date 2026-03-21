# scripts/shared_config.py — общее чтение shared-config.json и .env (в т.ч. image_protocol, CF_IMAGE_STORAGE_ROOT)
"""
Единая точка: загрузка конфига и переменных для агентов.
Импорт: from scripts.shared_config import get_config, get_image_protocol, get_image_storage_root, get_comfyui_config, get_comfyui_url
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _PROJECT_ROOT / "config" / "shared-config.json"
_ENV_PATH = _PROJECT_ROOT / "config" / ".env"

_config_cache: dict | None = None


def _load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        load_dotenv(_ENV_PATH)
        _config_cache = json.loads(_CONFIG_PATH.read_text("utf-8"))
    return _config_cache


def get_config() -> dict:
    """Весь shared-config.json (после load_dotenv)."""
    return _load_config()


def get_image_protocol() -> dict:
    """Блок image_protocol из конфига. Для agent8: count.min/max; для agent9: relative_path_pattern."""
    cfg = _load_config()
    return cfg.get("image_protocol") or {}


def get_comfyui_config() -> dict:
    """Блок comfyui из конфига: url, timeout, site_hero и т.д."""
    cfg = _load_config()
    return cfg.get("comfyui") or {}


def get_comfyui_url() -> str:
    """URL ComfyUI из COMFYUI_URL (.env) или url_default из конфига."""
    load_dotenv(_ENV_PATH)
    comfy = get_comfyui_config()
    env_name = comfy.get("url_env", "COMFYUI_URL")
    default = comfy.get("url_default", "http://127.0.0.1:8000")
    return os.getenv(env_name, "").strip() or default


def get_sd_webui_url() -> str:
    """URL Stable Diffusion WebUI (sdapi/v1/txt2img)."""
    load_dotenv(_ENV_PATH)
    comfy = get_comfyui_config()
    env_name = comfy.get("sd_webui_url_env", "SD_WEBUI_URL")
    default = comfy.get("sd_webui_url_default", "http://127.0.0.1:7860")
    return os.getenv(env_name, "").strip() or default


def get_sd_webui_root() -> str:
    """Путь к папке SD WebUI (root_env → .env → root_default из image_protocol.sd_webui)."""
    load_dotenv(_ENV_PATH)
    cfg = (get_config().get("image_protocol") or {}).get("sd_webui") or {}
    env_name = cfg.get("root_env", "SD_WEBUI_ROOT")
    default = cfg.get("root_default", "D:\\AI\\stable-diffusion-webui")
    return os.getenv(env_name, "").strip() or default


def get_image_storage_root() -> Path:
    """
    Корень хранилища картинок: из image_protocol берётся имя env (storage_root_env)
    и дефолт (storage_root_default); возвращается абсолютный путь (media/ в корне проекта, если переменная не задана).
    """
    load_dotenv(_ENV_PATH)
    cfg = get_image_protocol()
    env_name = cfg.get("storage_root_env", "CF_IMAGE_STORAGE_ROOT")
    default = cfg.get("storage_root_default", "media")
    root = os.getenv(env_name, "").strip() or default
    p = Path(root)
    return (p if p.is_absolute() else _PROJECT_ROOT / p).resolve()


def resolve_image_path(relative_path: str) -> Path:
    """Полный путь к файлу картинки: storage_root / relative_path."""
    root = get_image_storage_root()
    return root / relative_path.replace("/", os.sep).lstrip(os.sep)


# Какой вариант картинки использовать по умолчанию для каждого канала (жёстко для пайплайнов)
DEFAULT_IMAGE_VARIANT_BY_NETWORK = {
    "site": "hero",
    "vk": "feed",
    "insta": "square",
    "tg": "post",
    "wa": "post",
    "yt": "thumb",
    "ok": "thumb",
}


def get_image_path_for_network(
    image_rec: dict,
    network: str,
    variant_name: str | None = None,
) -> str | None:
    """
    Путь к картинке для канала: variants[network] с профилем variant_name.
    variant_name по умолчанию — DEFAULT_IMAGE_VARIANT_BY_NETWORK[network] (site→hero, vk→feed, insta→square, tg→post, wa→post).
    Для сториз/Reels передать variant_name="story".
    """
    variants = image_rec.get("variants") or {}
    channel_list = variants.get(network)
    if channel_list is None:
        return image_rec.get("image_path")
    if not isinstance(channel_list, list):
        return channel_list.get("image_path") if isinstance(channel_list, dict) else None
    name = variant_name or DEFAULT_IMAGE_VARIANT_BY_NETWORK.get(network, "post")
    for item in channel_list:
        if item.get("status") == "error":
            continue
        if item.get("name") == name:
            return item.get("image_path")
    if channel_list:
        for item in channel_list:
            if item.get("status") != "error":
                return item.get("image_path")
    return None


def build_image_relative_path(slug: str, index: int | str, *, year: int | None = None, month: int | None = None) -> str:
    """
    Подставляет в relative_path_pattern из image_protocol значения.
    По умолчанию year/month — текущие (UTC).
    """
    import datetime
    proto = get_image_protocol()
    pattern = proto.get("relative_path_pattern", "images/{year}/{month}/{slug}-{index}.jpg")
    now = datetime.datetime.utcnow()
    y = year if year is not None else now.year
    m = month if month is not None else now.month
    return pattern.format(year=y, month=f"{m:02d}", slug=slug, index=index)


def build_image_relative_path_with_size(
    slug: str,
    width: int,
    height: int,
    index: int,
    *,
    network: str = "site",
    variant: str = "hero",
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> str:
    """
    Путь: images/{year}/{month}/{day}/{slug}_{network}_{variant}_{width}x{height}_{index}.jpg
    variant — профиль размера (hero, thumb, feed, story, …).
    """
    import datetime
    proto = get_image_protocol()
    pattern = proto.get(
        "relative_path_pattern_with_size",
        "images/{year}/{month}/{day}/{slug}_{network}_{variant}_{width}x{height}_{index}.jpg",
    )
    now = datetime.datetime.utcnow()
    y = year if year is not None else now.year
    m = month if month is not None else now.month
    d = day if day is not None else now.day
    return pattern.format(
        year=y,
        month=f"{m:02d}",
        day=f"{d:02d}",
        slug=slug,
        network=network,
        variant=variant,
        width=width,
        height=height,
        index=index + 1,
    )
