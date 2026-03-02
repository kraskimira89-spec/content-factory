"""
agent9_images_runner.py

Агент 9: берёт план картинок от agent8 (images-plan.json),
генерирует изображения через Stable Diffusion / ComfyUI
и дописывает в JSON пути к файлам и размеры.
Пока: заглушка вместо реального вызова ComfyUI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Корень проекта content-factory — для импорта scripts.shared_config
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OUTPUT_DIR = _PROJECT_ROOT / "output"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.shared_config import (
    build_image_relative_path_with_size,
    get_image_protocol,
    get_image_storage_root,
)  # noqa: E402


def load_images_plan(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def fake_generate_image(prompt: str, width: int, height: int) -> tuple[bytes, int, int]:
    """
    ВРЕМЕННАЯ ЗАГЛУШКА.
    Вместо вызова ComfyUI возвращает пустые байты и заданный размер.
    """
    return b"", width, height


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

    for idx, img in enumerate(images):
        prompt = img.get("prompt", "")
        updated = dict(img)
        updated["variants"] = {}

        for network_name, profiles in variants_cfg.items():
            updated["variants"][network_name] = []
            for profile in profiles:
                name = profile.get("name", "default")
                width = profile.get("width", 1280)
                height = profile.get("height", 720)
                image_bytes, w, h = fake_generate_image(prompt, width, height)

                rel_path_str = build_image_relative_path_with_size(
                    slug, w, h, idx, network=network_name, variant=name
                )
                abs_path = (storage_root / rel_path_str).resolve()
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_bytes(image_bytes)

                print(f"[agent9] Картинка {idx + 1}/{len(images)} [{network_name}/{name}] -> {abs_path.name}")
                updated["variants"][network_name].append({
                    "name": name,
                    "image_path": rel_path_str.replace("\\", "/"),
                    "width": w,
                    "height": h,
                })

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

    print(f"[agent9] Генерация картинок для slug={slug} (все варианты из image_protocol.variants) ...")
    updated_plan = run_images_generation(plan, slug)

    print(f"[agent9] Сохранение обновлённого плана в {output_path}")
    save_generated_plan(output_path, updated_plan)

    print("[agent9] Готово (заглушка).")


if __name__ == "__main__":
    main()
