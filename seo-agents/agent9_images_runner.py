"""
agent9_images_runner.py

Агент 9: берёт план картинок от agent8 (images-plan.json),
генерирует изображения через SD WebUI / ComfyUI и дописывает пути в JSON.

URL не хардкодятся в коде — берутся из config/.env и config/shared-config.json:
- SD_WEBUI_URL (дефолт http://127.0.0.1:7860) — image_protocol.sd_webui
- COMFYUI_URL (дефолт http://127.0.0.1:8000) — comfyui.url_default

При ошибке подключения agent9 автоматически пробует порты 7860–7865 для SD.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Корень проекта content-factory — для импорта scripts.shared_config
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OUTPUT_DIR = _PROJECT_ROOT / "output"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.shared_config import (
    build_image_relative_path_with_size,
    get_comfyui_config,
    get_comfyui_url,
    get_image_protocol,
    get_image_storage_root,
    get_sd_webui_root,
    get_sd_webui_url,
)  # noqa: E402
from scripts.image_utils import save_image_bytes  # noqa: E402

# Кодировка вывода в консоль (русский текст без ошибок в Windows)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_sd_webui_config() -> dict:
    cfg = get_image_protocol()
    return cfg.get("sd_webui", {})


def load_images_plan(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _placeholder_image_bytes(width: int, height: int) -> bytes:
    """Минимальный валидный JPEG (серый прямоугольник) при недоступности SD/ComfyUI."""
    try:
        from PIL import Image
        import io
        img = Image.new("RGB", (max(1, width), max(1, height)), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return b""


def fake_generate_image(prompt: str, width: int, height: int) -> tuple[bytes, int, int]:
    """
    Заглушка при недоступности SD WebUI и ComfyUI.
    Возвращает серый JPEG заданного размера вместо пустых байт (чтобы не было битых/пустых файлов).
    """
    return _placeholder_image_bytes(width, height), width, height


def _check_sd_webui_ready(url: str, timeout: int = 5) -> bool:
    """Проверка: API SD WebUI доступен по URL."""
    try:
        r = requests.get(f"{url.rstrip('/')}/sdapi/v1/options", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def ensure_sd_webui_running(
    start_bat: str | None = None,
    poll_interval: int = 15,
    max_wait_sec: int = 600,
) -> None:
    """
    Если SD WebUI недоступен — запускает webui-user.bat и ждёт готовности API.
    start_bat: путь к webui-user.bat (по умолчанию {SD_WEBUI_ROOT}/webui-user.bat).
    """
    candidates = _get_sd_webui_candidate_urls()
    for url in candidates:
        if _check_sd_webui_ready(url):
            logger.info("SD WebUI уже запущен: %s", url)
            return

    # Ни один порт не отвечает — запускаем сервер
    root = Path(get_sd_webui_root())
    bat = start_bat or str(root / "webui-user.bat")
    if not Path(bat).exists():
        bat = str(root / "webui.bat")
    if not Path(bat).exists():
        raise FileNotFoundError(
            f"SD WebUI не запущен и не найден скрипт запуска: {bat}. "
            "Запустите вручную webui-user.bat из папки SD WebUI."
        )

    print("[agent9] SD WebUI не отвечает — запускаю сервер в отдельном окне…")
    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/c", bat],
            cwd=str(root),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        subprocess.Popen(
            [bat],
            cwd=str(root),
            start_new_session=True,
        )

    print(f"[agent9] Ожидание готовности API (макс. {max_wait_sec} с, проверка каждые {poll_interval} с)…")
    deadline = time.monotonic() + max_wait_sec
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        for url in candidates:
            if _check_sd_webui_ready(url):
                print(f"[agent9] SD WebUI готов: {url}")
                return
        print(f"[agent9] Ожидание… (осталось ~{int(deadline - time.monotonic())} с)")

    raise RuntimeError(
        f"SD WebUI не ответил за {max_wait_sec} с. Проверьте окно webui-user.bat и запустите agent9 снова."
    )


def _get_sd_webui_base_url() -> str:
    """base_url из env (SD_WEBUI_URL) или конфига."""
    import os
    sd_cfg = get_sd_webui_config()
    env_name = sd_cfg.get("base_url_env", "SD_WEBUI_URL")
    base_default = sd_cfg.get("base_url", "http://127.0.0.1:7860")
    return (os.getenv(env_name, "").strip() or base_default).rstrip("/")


def _get_sd_webui_candidate_urls() -> list[str]:
    """
    Список URL для перебора при ошибке подключения.
    Если 7860 занят, WebUI стартует на 7861, 7862… — пробуем по порядку.
    """
    from urllib.parse import urlparse

    base = _get_sd_webui_base_url()
    parsed = urlparse(base)
    host = parsed.hostname or "127.0.0.1"
    scheme = parsed.scheme or "http"
    try:
        port = parsed.port or 7860
    except (ValueError, TypeError):
        port = 7860

    # Порты 7860–7865 (если занят 7860, WebUI выдаёт 7861 и т.д.)
    all_ports = list(range(7860, 7866))
    # Сначала порт из .env, затем 7860–7865
    ports = [port] if port not in all_ports else [port] + [p for p in all_ports if p != port]

    return [f"{scheme}://{host}:{p}" for p in ports]


def _is_connection_error(exc: BaseException) -> bool:
    """Проверка: ошибка подключения (порт закрыт / connection refused)."""
    err_str = str(exc).lower()
    return (
        "connection" in err_str
        or "connection refused" in err_str
        or "connectionpool" in err_str
        or "failed to establish" in err_str
        or "10061" in err_str  # WinError connection refused
    )


def call_sd_webui_with_retry(
    payload: dict,
    max_retries: int | None = None,
    delay: float = 5.0,
    timeout: int = 180,
) -> dict:
    """
    Универсальный вызов SD WebUI с ретраями и перебором портов.
    При ошибке подключения (порт закрыт) — пробуем следующий порт (7861, 7862…).
    """
    sd_cfg = get_sd_webui_config()
    if max_retries is None:
        max_retries = int(sd_cfg.get("retries", 2)) + 1

    candidates = _get_sd_webui_candidate_urls()
    last_err = None

    for base_url in candidates:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("SD WebUI attempt %s/%s @ %s", attempt, max_retries, base_url)
                resp = requests.post(f"{base_url}/sdapi/v1/txt2img", json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                if "images" not in data or not data["images"]:
                    raise RuntimeError("SD WebUI response has no images")
                return data
            except Exception as e:
                last_err = e
                logger.warning("SD WebUI error on attempt %s @ %s: %s", attempt, base_url, e)
                if _is_connection_error(e):
                    # Порт закрыт — переходим к следующему кандидату
                    break
                if attempt < max_retries:
                    time.sleep(delay)

    raise RuntimeError(f"SD WebUI failed (tried ports 7860–7865): {last_err}")


def generate_image_sd_webui(abs_path: Path, prompt: str, width: int, height: int) -> tuple[int, int]:
    """Генерация через SD WebUI sdapi/v1/txt2img, настройки из image_protocol.sd_webui."""
    import base64

    sd_cfg = get_sd_webui_config()
    w = width or sd_cfg.get("default_width", 1280)
    h = height or sd_cfg.get("default_height", 720)

    payload = {
        "prompt": prompt,
        "negative_prompt": sd_cfg.get("negative_prompt", "blurry, low quality, distorted, text, watermark, logo"),
        "width": min(max(w, 512), 1536),
        "height": min(max(h, 512), 1536),
        "steps": sd_cfg.get("steps", 24),
        "cfg_scale": sd_cfg.get("cfg_scale", 7),
        "sampler_name": sd_cfg.get("sampler_name", "DPM++ 2M"),
        "batch_size": 1,
        "seed": -1,
    }
    if sd_cfg.get("checkpoint"):
        payload["override_settings"] = {"sd_model_checkpoint": sd_cfg["checkpoint"]}

    data = call_sd_webui_with_retry(payload, max_retries=3, delay=5.0)

    img_bytes = base64.b64decode(data["images"][0])
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    save_image_bytes(img_bytes, abs_path)

    return w, h


def _generate_via_sd_webui(prompt: str, width: int, height: int, timeout: int) -> bytes:
    """Stable Diffusion WebUI sdapi/v1/txt2img — возвращает байты PNG."""
    import base64

    sd_cfg = get_sd_webui_config()
    payload = {
        "prompt": prompt,
        "negative_prompt": sd_cfg.get("negative_prompt", "blurry, low quality, distorted, text, watermark, logo"),
        "width": min(max(width, 512), 1536),
        "height": min(max(height, 512), 1536),
        "steps": sd_cfg.get("steps", 24),
        "sampler_name": sd_cfg.get("sampler_name", "DPM++ 2M"),
        "cfg_scale": sd_cfg.get("cfg_scale", 7),
        "seed": -1,
    }
    if sd_cfg.get("checkpoint"):
        payload["override_settings"] = {"sd_model_checkpoint": sd_cfg["checkpoint"]}
    data = call_sd_webui_with_retry(payload, timeout=timeout)
    return base64.b64decode(data["images"][0])


def run_comfyui_generation(abs_path: Path, prompt: str, width: int, height: int) -> tuple[int, int]:
    """
    Генерация через: 1) ComfyUI/API /generate, 2) SD WebUI sdapi/v1/txt2img.
    При ошибке — заглушка (серый JPEG).
    """
    base_url = get_comfyui_url().strip().rstrip("/")
    sd_url = get_sd_webui_url().strip().rstrip("/")
    comfy_cfg = get_comfyui_config()
    timeout = int(comfy_cfg.get("timeout_sec", 120))
    # 1) SD WebUI sdapi/v1/txt2img (порт 7860) — приоритет, не требует доп. сервера
    if sd_url:
        try:
            img_bytes = _generate_via_sd_webui(prompt, width, height, timeout)
            save_image_bytes(img_bytes, abs_path)
            return width, height
        except Exception as e:
            print(f"[agent9] SD WebUI недоступен: {e}")

    # 2) ComfyUI (часто :8000 в ComfyUI 0.15+) или Flask image_generate_api на своём порту
    if base_url:
        try:
            resp = requests.post(
                f"{base_url}/generate",
                json={"prompt": prompt, "width": width, "height": height},
                timeout=timeout,
            )
            resp.raise_for_status()
            save_image_bytes(resp.content, abs_path)
            return width, height
        except Exception as e:
            print(f"[agent9] ComfyUI /generate недоступен: {e}")

    # 3) Fallback — серый JPEG (placeholder)
    image_bytes, w, h = fake_generate_image(prompt, width, height)
    save_image_bytes(image_bytes, abs_path)
    return w, h


def _normalize_variants_cfg(variants_cfg: dict) -> dict[str, list[dict]]:
    """Приводит variants к виду { network: [ { name, width, height }, ... ] }."""
    out: dict[str, list[dict]] = {}
    default_list = [{"name": "hero", "width": 1280, "height": 720}]
    for network_name, val in (variants_cfg or {"site": default_list}).items():
        if isinstance(val, list):
            out[network_name] = val
        elif isinstance(val, dict) and ("width" in val or "height" in val):
            out[network_name] = [{"name": val.get("name", "default"), "width": val.get("width", 1280), "height": val.get("height", 720)}]
        else:
            out[network_name] = default_list
    return out


def _count_total_variants(variants_cfg: dict[str, list], num_images: int) -> int:
    """Общее число картинок к генерации: изображения × варианты (сети × профили)."""
    total = 0
    for profiles in variants_cfg.values():
        total += len(profiles) * num_images
    return total


def run_images_generation(plan: dict[str, Any], slug: str) -> dict[str, Any]:
    """
    Для каждой картинки проходим по всем сетям и профилям из image_protocol.variants,
    генерируем файл под каждый (network, variant) и заполняем image.variants[network] = [ { name, image_path, width, height }, ... ].
    """
    protocol = get_image_protocol()
    variants_cfg = _normalize_variants_cfg(protocol.get("variants"))
    images = plan.get("images", [])
    updated_images: list[dict[str, Any]] = []
    storage_root = get_image_storage_root()
    total = _count_total_variants(variants_cfg, len(images))
    current = 0

    for idx, img in enumerate(images):
        base_prompt = img.get("prompt", "")
        base_style = img.get("style", "realistic photo")
        base_alt = img.get("alt", "")
        variant_overrides = img.get("variant_overrides") or {}
        updated = dict(img)
        updated["variants"] = {}

        for network_name, profiles in variants_cfg.items():
            updated["variants"][network_name] = []
            for profile in profiles:
                name = profile.get("name", "default")
                override_key = f"{network_name}.{name}"
                override = variant_overrides.get(override_key)
                if override:
                    prompt = override.get("prompt", base_prompt)
                    alt = override.get("alt", base_alt)
                else:
                    prompt = base_prompt
                    alt = base_alt
                width = profile.get("width", 1280)
                height = profile.get("height", 720)
                current += 1

                rel_path_str = build_image_relative_path_with_size(
                    slug, width, height, idx, network=network_name, variant=name
                )
                abs_path = (storage_root / rel_path_str).resolve()

                print(f"  [ {current:3d}/{total} ] {network_name}/{name} -> {abs_path.name}")
                variant_ok = True
                gen_width = width or 1280
                gen_height = height or 720
                if network_name == "site" and name == "hero":
                    w, h = run_comfyui_generation(abs_path, prompt, width, height)
                    if abs_path.exists() and abs_path.stat().st_size == 0:
                        variant_ok = False
                else:
                    try:
                        w, h = generate_image_sd_webui(abs_path, prompt, gen_width, gen_height)
                    except Exception as e:
                        logger.error(
                            "Failed to generate image for slug=%s, %s/%s, prompt=%s...: %s",
                            slug, network_name, name, (prompt[:50] + "..." if len(prompt) > 50 else prompt), e
                        )
                        variant_ok = False
                        w, h = width, height
                        if abs_path.exists() and abs_path.stat().st_size == 0:
                            try:
                                abs_path.unlink()
                            except OSError:
                                pass

                variant_rec = {
                    "name": name,
                    "image_path": rel_path_str.replace("\\", "/"),
                    "width": w,
                    "height": h,
                }
                if not variant_ok:
                    variant_rec["status"] = "error"
                    variant_rec["error"] = "SD WebUI: генерация не удалась после ретраев"
                updated["variants"][network_name].append(variant_rec)

        # Для первого изображения: hero alt из override подставляем в image.alt (agent4 использует для featured)
        if idx == 0 and variant_overrides.get("site.hero"):
            hero_override_alt = variant_overrides["site.hero"].get("alt")
            if hero_override_alt:
                updated["alt"] = hero_override_alt

        updated_images.append(updated)

    plan["images"] = updated_images
    return plan


def save_generated_plan(output_path: Path, plan: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _get_latest_plan_json() -> Path:
    """Последний по времени *.images-plan.json в output/ (для запуска без аргументов)."""
    if not _OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Папка output не найдена: {_OUTPUT_DIR}")
    files = sorted(_OUTPUT_DIR.glob("*.images-plan.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"В {_OUTPUT_DIR} нет файлов *.images-plan.json (сначала запустите agent8)")
    return files[-1]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Agent9: генератор картинок (пока заглушка)")
    parser.add_argument(
        "--plan-json",
        type=str,
        default=None,
        help="Путь к JSON от agent8 (без указания — последний *.images-plan.json в output)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Путь к выходному JSON (без указания — {stem}.images-generated.json рядом с планом)",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="slug услуги/страницы для имён файлов (по умолчанию из плана: service_slug)",
    )
    args = parser.parse_args()

    if args.plan_json is None and args.output_json is None:
        plan_path = _get_latest_plan_json()
        base = plan_path.stem.replace(".images-plan", "")
        output_path = plan_path.parent / (base + ".images-generated.json")
        print(f"[agent9] Режим по умолчанию: последний план = {plan_path.name}")
    elif args.plan_json and args.output_json:
        plan_path = Path(args.plan_json)
        output_path = Path(args.output_json)
    else:
        raise SystemExit("Укажите оба --plan-json и --output-json либо оба опустите (автовыбор последнего плана).")

    print(f"[agent9] Загрузка плана из {plan_path}")
    plan = load_images_plan(plan_path)

    slug = args.slug or plan.get("service_slug", "service")

    total = _count_total_variants(
        _normalize_variants_cfg(get_image_protocol().get("variants")),
        len(plan.get("images", [])),
    )
    print(f"[agent9] Генерация картинок для slug={slug}: всего {total} вариантов")
    ensure_sd_webui_running()
    print()
    updated_plan = run_images_generation(plan, slug)

    save_generated_plan(output_path, updated_plan)

    # Итог: список путей и путь к JSON
    generated_paths: list[str] = []
    for img in updated_plan.get("images", []):
        for net, variants in (img.get("variants") or {}).items():
            for v in variants:
                p = v.get("image_path")
                if p:
                    generated_paths.append(p)
    print()
    print("=" * 60)
    print("  РЕЗУЛЬТАТ ГЕНЕРАЦИИ")
    print("=" * 60)
    print(f"  Сгенерировано картинок: {len(generated_paths)}")
    print(f"  План с путями сохранён:  {output_path}")
    print(f"  Папка с файлами:         {get_image_storage_root()}")
    print()
    if generated_paths:
        print("  Файлы:")
        for p in generated_paths[:20]:
            print(f"    {p}")
        if len(generated_paths) > 20:
            print(f"    ... и ещё {len(generated_paths) - 20}")
    print("=" * 60)


if __name__ == "__main__":
    main()
