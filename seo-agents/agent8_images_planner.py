"""
agent8_images_planner.py

Агент 8: придумывает промпты и alt-тексты для картинок
по готовому тексту статьи. Извлекает глубинный смысл из H2-блоков,
создаёт символичные промпты для эмоциональной поддержки текста.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Корень проекта content-factory
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SEO_AGENTS = _PROJECT_ROOT / "seo-agents"
_OUTPUT_DIR = _PROJECT_ROOT / "output"

for p in (_PROJECT_ROOT, str(_SEO_AGENTS / "shared")):
    if p not in sys.path:
        sys.path.insert(0, str(p))

from scripts.shared_config import get_image_protocol  # noqa: E402
from api_client import ask_ai  # noqa: E402

PROMPT_FILE = _PROJECT_ROOT / "prompts" / "agents" / "agent8_images.txt"


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


SLOT_PATTERN = re.compile(r"<!--\s*image_slot:\s*(\w+)\s*-->", re.IGNORECASE)


def _parse_blocks_by_slots(md_text: str) -> list[dict[str, Any]]:
    """
    Парсит markdown по <!-- image_slot: X --> (после H2).
    Структура: ## H2 → <!-- image_slot: X --> → текст блока.
    Возвращает [{ slot, title, text }, ...] — только блоки с картинками.
    """
    blocks: list[dict[str, Any]] = []
    lines = md_text.split("\n")
    current_title = ""
    current_slot: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_slot:
                blocks.append({
                    "slot": current_slot,
                    "title": current_title,
                    "text": "\n".join(current_lines).strip(),
                })
            current_title = line[3:].strip()
            current_slot = None
            current_lines = []
            continue
        m = SLOT_PATTERN.search(line)
        if m:
            current_slot = m.group(1).lower()
            current_lines = []
            continue
        if current_slot:
            current_lines.append(line)

    if current_slot:
        blocks.append({
            "slot": current_slot,
            "title": current_title,
            "text": "\n".join(current_lines).strip(),
        })

    return blocks


def _parse_h2_blocks(md_text: str) -> list[tuple[str, str]]:
    """Разбивает markdown на блоки по H2. Возвращает [(заголовок_h2, текст_блока), ...]."""
    blocks: list[tuple[str, str]] = []
    lines = md_text.split("\n")
    current_block: list[str] = []
    current_title = ""

    for line in lines:
        if line.startswith("## "):
            if current_block or current_title:
                blocks.append((current_title or "Лид", "\n".join(current_block).strip()))
            current_title = line[3:].strip()
            current_block = []
        else:
            current_block.append(line)

    if current_block or current_title:
        blocks.append((current_title or "Лид", "\n".join(current_block).strip()))

    return blocks


def _load_system_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8").strip()
    return "Создай JSON: prompt, style, alt"


def _ask_prompt_for_block(block: dict[str, Any], service_name: str) -> dict[str, Any]:
    """Для одного блока (slot, title, text) получает промпт от AI."""
    system = _load_system_prompt()
    user = (
        f"Услуга: {service_name}. Слот: {block['slot']}. Заголовок: {block['title']}\n\n"
        f"Текст блока:\n{block['text'][:500]}\n\n"
        "Выдай промпт для эмоционально поддерживающей картинки. Только JSON."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        raw = ask_ai(messages, max_tokens=800)
        text = raw.strip()
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)
    except Exception:
        return {
            "prompt": f"Wellness center, {service_name}, {block['slot']}, calm, no faces",
            "style": "realistic photo",
            "alt": f"{service_name} — {block.get('title', '')}",
        }


def plan_images_for_post(context: dict[str, Any]) -> dict[str, Any]:
    """
    Парсит markdown по <!-- image_slot: X -->, для каждого блока генерирует эмоциональный промпт.
    Выход: { images: [{ slot, prompt, alt, layout }, ...], blocks: [...] }
    """
    meta = context.get("meta", {})
    service_slug = meta.get("service_slug", "service")
    service_name = meta.get("service_name", "Услуга")
    md_text = context.get("markdown", "")

    # Сначала пробуем слоты
    blocks = _parse_blocks_by_slots(md_text)
    images: list[dict[str, Any]] = []

    if blocks:
        # Режим слотов: для каждого блока — свой промпт
        layouts = ["right", "left", "below"]
        for idx, block in enumerate(blocks):
            ai_result = _ask_prompt_for_block(block, service_name)
            layout = layouts[idx % 3] if idx < 4 else "below"
            images.append({
                "slot": block["slot"],
                "prompt": ai_result.get("prompt", ""),
                "style": ai_result.get("style", "realistic photo"),
                "alt": ai_result.get("alt", f"{service_name} — {block.get('title', '')}"),
                "layout": layout,
                "role": "emotion_support",
            })
    else:
        # Fallback: без слотов, по H2
        h2_blocks = _parse_h2_blocks(md_text)
        blocks_summary = "\n\n".join(
            f"[Блок {i}] {title}\n{text[:400]}{'...' if len(text) > 400 else ''}"
            for i, (title, text) in enumerate(h2_blocks)
        )
        system = "Создай JSON с images: prompt, alt, insert_after_block, layout."
        user = (
            f"Услуга: {service_name}. Текст:\n\n{blocks_summary}\n\n"
            "Создай 2–4 изображения с символичными промптами. Только JSON."
        )
        try:
            raw = ask_ai([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=2000)
            text = raw.strip()
            if "```" in text:
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if m:
                    text = m.group(1).strip()
            data = json.loads(text)
            images = data.get("images", [])
            for i, img in enumerate(images):
                if "insert_after_block" not in img:
                    img["insert_after_block"] = min(i, len(h2_blocks) - 1)
                if "layout" not in img:
                    img["layout"] = ("right" if i % 2 == 0 else "left") if i < 3 else "below"
        except Exception:
            images = [{
                "prompt": f"Modern wellness center, {service_name}, calm, no faces, no logos",
                "style": "realistic photo",
                "alt": f"{service_name} в центре здоровья Энтузиаст",
                "insert_after_block": 0,
                "layout": "below",
            }]

    return {
        "images": images,
        "service_slug": service_slug,
        "blocks": blocks if blocks else None,
    }


def save_images_plan(output_path: Path, plan: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _get_latest_page_md() -> Path:
    """Последний по времени *_page_*.md в output/ (для запуска без аргументов)."""
    if not _OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Папка output не найдена: {_OUTPUT_DIR}")
    files = sorted(_OUTPUT_DIR.glob("*_page_*.md"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"В {_OUTPUT_DIR} нет файлов *_page_*.md")
    return files[-1]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Agent8: планировщик картинок")
    parser.add_argument(
        "--input-md",
        type=str,
        default=None,
        help="Путь к markdown-файлу поста (без указания — последний *_page_*.md из output)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Путь к JSON плана (без указания — {stem}.images-plan.json рядом с .md)",
    )

    args = parser.parse_args()

    if args.input_md is None and args.output_json is None:
        input_path = _get_latest_page_md()
        output_path = input_path.parent / (input_path.stem + ".images-plan.json")
        print(f"[agent8] Режим по умолчанию: последний .md = {input_path.name}")
    elif args.input_md and args.output_json:
        input_path = Path(args.input_md)
        output_path = Path(args.output_json)
    else:
        raise SystemExit("Укажите оба --input-md и --output-json либо оба опустите (автовыбор последнего .md).")

    print(f"[agent8] Загрузка контекста из {input_path}")
    context = load_post_context(input_path)

    print("[agent8] Планирование картинок...")
    plan = plan_images_for_post(context)

    print(f"[agent8] Сохранение плана в {output_path}")
    save_images_plan(output_path, plan)

    # Отдельный JSON с блоками (гибрид: markdown + JSON для agent8)
    if plan.get("blocks"):
        blocks_path = output_path.with_name(
            output_path.stem.replace(".images-plan", "") + ".blocks.json"
        )
        blocks_path.write_text(
            json.dumps(
                {"blocks": plan["blocks"], "service_slug": plan.get("service_slug")},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[agent8] Блоки сохранены в {blocks_path.name}")

    print("[agent8] Готово.")


if __name__ == "__main__":
    main()
