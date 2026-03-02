"""
agent8_images_planner.py

Агент 8: придумывает промпты и alt-тексты для картинок
по готовому тексту статьи и метаданным услуги.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Корень проекта content-factory — для импорта scripts.shared_config
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.shared_config import get_image_protocol  # noqa: E402
# сюда позже добавим импорт LLM-клиента (локального/Perplexity/и т.п.)


def load_post_context(input_path: Path) -> dict[str, Any]:
    """
    Загружает контекст для генерации картинок.
    Простейший вариант: читаем markdown-файл и метаданные из JSON рядом.
    """
    md_text = input_path.read_text(encoding="utf-8")

    meta_path = input_path.with_suffix(".meta.json")
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    return {
        "markdown": md_text,
        "meta": meta,
    }


def plan_images_for_post(context: dict[str, Any]) -> dict[str, Any]:
    """
    Генерирует структуру images по контракту image_protocol (пока без вызова модели).
    """
    image_cfg = get_image_protocol()
    count_cfg = image_cfg.get("count", {})
    min_count = count_cfg.get("min", 1)
    max_count = count_cfg.get("max", 3)

    # Пока делаем заглушку: фиксированное число 1 (потом добавим генерацию через LLM)
    num_images = max(min_count, 1)
    if num_images > max_count:
        num_images = max_count

    # Простая заглушка на основе метаданных
    meta = context.get("meta", {})
    service_slug = meta.get("service_slug", "service")
    service_name = meta.get("service_name", "Услуга центра здоровья")

    images: list[dict[str, Any]] = []

    for index in range(num_images):
        prompt = (
            f"High-quality photo of {service_name} (pressotherapy) procedure in a modern health and wellness center, "
            f"clean interior, calm atmosphere, professional medical equipment, no faces, no logos, no text. "
            f"Процедура {service_name} в современном оздоровительном центре, чистое светлое помещение, "
            f"профессиональное оборудование, спокойная расслабляющая атмосфера, без лиц и без логотипов."
        )
        alt = f"{service_name} в центре здоровья Энтузиаст, Ноябрьск"

        images.append(
            {
                "prompt": prompt,
                "style": "realistic photo",
                "alt": alt,
                # image_path заполняет уже agent9 после генерации
            }
        )

    return {"images": images, "service_slug": service_slug}


def save_images_plan(output_path: Path, plan: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Agent8: планировщик картинок")
    parser.add_argument(
        "--input-md",
        type=str,
        required=True,
        help="Путь к markdown-файлу поста (output/*.md)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Куда сохранить JSON с планом картинок (images-plan.json)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_md)
    output_path = Path(args.output_json)

    print(f"[agent8] Загрузка контекста из {input_path}")
    context = load_post_context(input_path)

    print("[agent8] Планирование картинок...")
    plan = plan_images_for_post(context)

    print(f"[agent8] Сохранение плана в {output_path}")
    save_images_plan(output_path, plan)

    print("[agent8] Готово.")


if __name__ == "__main__":
    main()
