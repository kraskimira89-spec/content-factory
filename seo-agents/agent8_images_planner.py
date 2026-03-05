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

# Маппинг slug → английское название для промптов SD (Flux)
SERVICE_EN_BY_SLUG: dict[str, str] = {
    "aromaterapiya": "aromatherapy",
    "pressoterapiya": "pressotherapy",
    "fitobochka": "cedar sauna",
    "solyanaya-komnata": "salt room",
    "massazh": "massage",
    "vlok": "VLOK",
    "uglekislaya-vanna": "dry CO2 bath",
    "gidromassazh": "hydrotherapy massage",
    "limfodrenazh-nog": "lymphatic drainage",
    "karboksiterapiya": "carboxytherapy",
    "fitoparolechenie": "herbal steam therapy",
    "galoterapiya": "halotherapy salt room",
    "infrakrasnaya-sauna": "infrared sauna",
}

SLOT_PROMPTS: dict[str, dict[str, str]] = {
    "problems": {
        "prompt_en": (
            "A dimly lit living room scene suggesting chronic fatigue and stress: "
            "empty couch, messy desk with scattered papers in the background, "
            "coffee cup, rumpled blanket, "
            "cool blue desaturated color palette, soft window light, shallow depth of field, "
            "realistic photo, 50mm lens, f/2.8 aperture, "
            "clean composition, no people, no persons"
        ),
        "prompt_ru": (
            "Сцена в комнате с приглушенным светом, показывающая хроническую усталость и стресс: "
            "человек сидит один на диване с закрытыми глазами и массирует виски, "
            "на заднем плане беспорядок на столе, "
            "холодная приглушенная палитра, мягкий свет из окна, малая глубина резкости, "
            "реалистичное фото, чистая композиция, свободное место для текста"
        ),
        "alt_template": "Проблемы, с которыми помогает справиться {service_ru}",
        "style": "realistic photo",
    },
    "mechanism": {
        "prompt_en": (
            "Close-up of {service_en} essential oils and aroma diffuser on a wooden tray, "
            "visible warm steam rising, soft golden backlight, "
            "lavender sprigs and eucalyptus leaves arranged neatly, "
            "shallow depth of field, creamy bokeh background, "
            "realistic macro photo, warm color temperature, "
            "clean unmarked glass bottles, professional product lighting, no people"
        ),
        "prompt_ru": (
            "Крупный план эфирных масел и аромадиффузора для {service_ru} на деревянном подносе, "
            "виден теплый пар, мягкая золотистая подсветка, "
            "аккуратно разложенные веточки лаванды и эвкалипта, "
            "малая глубина резкости, мягкий боке-фон, "
            "реалистичное макро-фото с аккуратными не подписанными бутылочками"
        ),
        "alt_template": "Как действует {service_ru}: эфирные масла и аромадиффузор",
        "style": "realistic photo",
    },
    "process": {
        "prompt_en": (
            "High-end spa photography of {service_en} treatment room in a modern health center, "
            "massage table with neatly folded white towels, "
            "aroma diffuser with soft visible steam on a wooden side table, "
            "two candles and a small green plant, "
            "soft warm studio lighting, beige and white interior, "
            "wide angle shot, 35mm lens, f/4, realistic photo, "
            "clean composition, no text, no logo, no people, empty room"
        ),
        "prompt_ru": (
            "Спокойный кабинет для {service_ru} в современном центре здоровья в Ноябрьске: "
            "массажный стол с аккуратно сложенными белыми полотенцами, "
            "аромадиффузор с мягким паром, две свечи на деревянной полке, "
            "зеленое растение в углу, мягкий теплый свет, "
            "бежево-белый интерьер, широкоугольный реалистичный снимок пустого кабинета"
        ),
        "alt_template": "Кабинет {service_ru} в центре здоровья «Энтузиаст» в Ноябрьске",
        "style": "realistic photo",
    },
    "result": {
        "prompt_en": (
            "Bright airy spa relaxation lounge after a {service_en} session, "
            "empty daybed with soft white robe neatly draped, "
            "large window with warm morning sunlight, "
            "fresh flowers in a vase and a cup of herbal tea on a side table, "
            "warm golden color palette, realistic photo, peaceful welcoming atmosphere, "
            "no people, unoccupied scene"
        ),
        "prompt_ru": (
            "Светлая комната отдыха после сеанса {service_ru}: "
            "человек в мягком белом халате отдыхает на шезлонге, "
            "легкая улыбка, закрытые глаза, полностью расслабленная поза, "
            "большое окно с теплым утренним светом, "
            "свежие цветы в вазе и чашка травяного чая на столике, "
            "теплая золотистая палитра, реалистичное фото, атмосфера спокойствия"
        ),
        "alt_template": "Результат после курса {service_ru}: расслабление и хорошее самочувствие",
        "style": "realistic photo",
    },
    "target_audience": {
        "prompt_en": (
            "Editorial style still life suggesting who benefits from {service_en}: "
            "empty office desk with coffee and papers, yoga mat and water bottle, "
            "comfortable armchair with a book and reading glasses, "
            "soft natural daylight, muted warm tones, modern lifestyle aesthetic, "
            "realistic photo, clean minimal backgrounds, no people"
        ),
        "prompt_ru": (
            "Коллаж в журнальном стиле из трех людей, которым полезна {service_ru}: "
            "уставший офисный сотрудник за столом, "
            "активная женщина после тренировки, делающая растяжку, "
            "спокойный человек среднего возраста с книгой дома, "
            "мягкий дневной свет, теплые оттенки, современная лайфстайл-эстетика, "
            "реалистичное фото с минималистичным фоном"
        ),
        "alt_template": "Кому особенно полезна {service_ru}",
        "style": "realistic photo",
    },
    "faq": {
        "prompt_en": (
            "Flat lay overhead shot of {service_en} preparation items on a light wooden surface: "
            "small amber glass bottles with essential oils, dried lavender bundles, "
            "a white ceramic aroma diffuser, a notepad and pen, "
            "eucalyptus branch, soft even overhead lighting, "
            "realistic product photography, clean organized composition, "
            "unmarked labels, warm natural colors, no people"
        ),
        "prompt_ru": (
            "Вид сверху на предметы для подготовки к {service_ru} на светлой деревянной поверхности: "
            "небольшие коричневые бутылочки с эфирными маслами, "
            "сухие веточки лаванды, белый керамический аромадиффузор, "
            "блокнот и ручка, веточка эвкалипта, "
            "мягкий ровный свет сверху, аккуратная композиция без надписей"
        ),
        "alt_template": "Частые вопросы об услуге {service_ru}",
        "style": "realistic photo",
    },
    "utp": {
        "prompt_en": (
            "A welcoming reception area of a modern health and wellness center in Noyabrsk, "
            "clean minimalist interior with warm wood accents and green plants, "
            "soft ambient lighting, comfortable seating area, "
            "shelf with neatly arranged skincare and {service_en} essential oils, "
            "realistic interior photo, bright inviting atmosphere, no people, empty reception"
        ),
        "prompt_ru": (
            "Уютная зона ресепшн современного центра здоровья в Ноябрьске: "
            "чистый минималистичный интерьер с теплыми деревянными акцентами и зелеными растениями, "
            "мягкий рассеянный свет, удобные кресла, "
            "полка с аккуратно расставленными средствами по уходу и эфирными маслами для {service_ru}, "
            "реалистичное интерьерное фото с дружелюбной атмосферой"
        ),
        "alt_template": "Почему выбирают {service_ru} в центре здоровья «Энтузиаст»",
        "style": "realistic photo",
    },
}

DEFAULT_SLOT = "process"


def _parse_service_from_filename(md_path: Path) -> tuple[str | None, str | None]:
    """Из *_page_{услуга}_{город}.md извлекает (service_name, city)."""
    name = md_path.stem
    parts = name.split("_page_")
    if len(parts) != 2 or "approved" in parts[1].lower():
        return None, None
    tail_parts = parts[1].split("_")
    if len(tail_parts) < 2:
        return None, None
    city = tail_parts[-1]
    service = " ".join(tail_parts[:-1])
    return service or None, city or None


def _resolve_slug_from_name(service_name: str) -> str:
    """По имени услуги возвращает slug из shared-config (uslugi + services)."""
    from scripts.shared_config import get_config
    cfg = get_config()
    for section in (cfg.get("uslugi", {}), cfg.get("services", {})):
        for slug, svc in section.items():
            if (svc.get("name") or "").strip().lower() == (service_name or "").strip().lower():
                return slug
            for alias in svc.get("aliases", []):
                if (alias or "").strip().lower() == (service_name or "").strip().lower():
                    return slug
    return "service"


def load_post_context(input_path: Path) -> dict[str, Any]:
    """
    Загружает контекст для генерации картинок.
    Простейший вариант: читаем markdown-файл и метаданные из JSON рядом.
    Если meta пустой — берём service_name и city из имени файла.
    """
    md_text = input_path.read_text(encoding="utf-8")

    meta_path = input_path.with_suffix(".meta.json")
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    parsed_name, parsed_city = _parse_service_from_filename(input_path)
    if parsed_name and (not meta.get("service_slug") or meta.get("service_slug") == "service"):
        meta["service_name"] = meta.get("service_name") or parsed_name
        meta["service_slug"] = _resolve_slug_from_name(parsed_name)
    if parsed_city and not meta.get("city"):
        meta["city"] = parsed_city

    return {
        "markdown": md_text,
        "meta": meta,
        "input_path": input_path,
    }


SLOT_PATTERN = re.compile(r"<!--\s*image_slot:\s*(\w+)\s*-->", re.IGNORECASE)


def _service_en(service_slug: str, service_name: str) -> str:
    """Английское название услуги для промптов SD."""
    slug = (service_slug or "").strip().lower()
    if slug in SERVICE_EN_BY_SLUG:
        return SERVICE_EN_BY_SLUG[slug]
    # Fallback: берём первое слово или транслитерируем slug
    name_lower = (service_name or "").strip().lower()
    if "арома" in name_lower or "aroma" in slug:
        return "aromatherapy"
    if "прессо" in name_lower or "presso" in slug:
        return "pressotherapy"
    if "фито" in name_lower or "кедр" in name_lower:
        return "cedar sauna"
    if "солян" in name_lower:
        return "salt room"
    return slug.replace("-", " ") if slug else "wellness procedure"


def build_prompt_for_slot(
    slot: str,
    service_ru: str,
    service_en: str,
) -> tuple[str, str, str]:
    """
    Собирает промпт для слота из таблицы SLOT_PROMPTS.

    Возвращает:
        prompt  — англ + рус в одной строке (для SD)
        alt     — alt-текст по-русски
        style   — стиль ("realistic photo" и т.п.)
    """
    key = (slot or "").strip().lower()

    # targetaudience в markdown → target_audience в таблице
    if key == "targetaudience":
        key = "target_audience"
    if key == "procedure":
        key = "process"

    cfg = SLOT_PROMPTS.get(key)
    if cfg is None:
        cfg = SLOT_PROMPTS[DEFAULT_SLOT]

    prompt_en = cfg["prompt_en"].format(service_en=service_en, service_ru=service_ru)
    prompt_ru = cfg["prompt_ru"].format(service_en=service_en, service_ru=service_ru)

    # Только английский для SD 1.5 — без смешения языков
    prompt = prompt_en

    alt = cfg["alt_template"].format(service_ru=service_ru, service_en=service_en)
    style = cfg.get("style", "realistic photo")

    return prompt, alt, style


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
        # Лимит изображений: в режиме теста (test_slug + test_max_images) — меньше, иначе count.max
        protocol = get_image_protocol()
        count_cfg = protocol.get("count", {})
        test_slug = protocol.get("test_slug")
        test_max = protocol.get("test_max_images")
        if test_slug and str(service_slug).strip().lower() == str(test_slug).strip().lower() and test_max is not None:
            max_images = int(test_max)
        else:
            max_images = int(count_cfg.get("max", 4))
        blocks = blocks[:max_images]

        service_en = _service_en(service_slug, service_name)

        layouts = ["right", "left", "below"]
        for idx, block in enumerate(blocks):
            slot = block.get("slot", DEFAULT_SLOT)
            prompt, alt_ru, style = build_prompt_for_slot(
                slot=slot,
                service_ru=service_name,
                service_en=service_en,
            )
            layout = layouts[idx % 3] if idx < 4 else "below"
            images.append({
                "slot": slot,
                "prompt": prompt,
                "style": style,
                "alt": alt_ru,
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
