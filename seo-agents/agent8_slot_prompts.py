# =============================================================================
#  SLOT_PROMPTS — таблица промптов для каждого блока страницы
#  Все промпты на английском (Flux лучше понимает EN).
#  Flux НЕ поддерживает negative_prompt — поэтому вместо "no text, no faces"
#  используем позитивные замены: "clean unmarked surfaces", "empty room", и т.д.
#
#  Каждый слот содержит:
#    prompt_template — шаблон с {service_en} и {service_ru}
#    alt_template    — шаблон alt-текста (рус, для SEO)
#    style           — стиль генерации
# =============================================================================

SLOT_PROMPTS: dict[str, dict[str, str]] = {

    # ── Проблемы, с которыми приходят клиенты ────────────────────────────
    "problems": {
        "prompt_template": (
            "A dimly lit living room scene showing signs of chronic fatigue and stress: "
            "a person sitting alone on a couch with closed eyes, rubbing temples, "
            "messy desk with scattered papers in the background, "
            "cool blue desaturated color palette, soft window light, shallow depth of field, "
            "realistic photo, 50mm lens, f/2.8 aperture, "
            "clean composition with empty foreground space"
        ),
        "alt_template": "Проблемы, с которыми помогает {service_ru}: стресс и усталость",
        "style": "realistic photo",
    },

    # ── Механизм действия процедуры ──────────────────────────────────────
    "mechanism": {
        "prompt_template": (
            "Close-up of {service_en} essential oils and aroma diffuser on a wooden tray, "
            "visible warm steam rising, soft golden backlight, "
            "lavender sprigs and eucalyptus leaves arranged neatly, "
            "shallow depth of field, creamy bokeh background, "
            "realistic macro photo, warm color temperature 3200K, "
            "clean unmarked surfaces, professional product photography"
        ),
        "alt_template": "Как работает {service_ru}: эфирные масла и аромадиффузор",
        "style": "realistic photo",
    },

    # ── Как проходит процедура (основной process-кадр) ───────────────────
    "process": {
        "prompt_template": (
            "A tranquil {service_en} treatment room in a modern health center, "
            "massage table with neatly folded white towels, "
            "aroma diffuser emitting soft visible steam, "
            "two warm candles on a wooden shelf, potted green plant in the corner, "
            "soft warm ambient light, beige and white interior, "
            "wide angle shot, realistic photo, 35mm lens, f/4 aperture, "
            "peaceful solitary empty room, polished surfaces"
        ),
        "alt_template": "Кабинет {service_ru} в центре здоровья «Энтузиаст» в Ноябрьске",
        "style": "realistic photo",
    },

    # ── Результат после курса процедур ───────────────────────────────────
    "result": {
        "prompt_template": (
            "Bright airy spa relaxation lounge after a {service_en} session, "
            "person wrapped in soft white robe resting on a comfortable daybed, "
            "gentle smile, eyes closed, completely relaxed posture, "
            "large window with warm morning sunlight streaming in, "
            "fresh flowers in a vase, cup of herbal tea on a side table, "
            "warm golden color palette, realistic photo, 85mm portrait lens, "
            "f/2.0 aperture, creamy bokeh, peaceful welcoming atmosphere"
        ),
        "alt_template": "Результат после курса {service_ru}: расслабление и хорошее самочувствие",
        "style": "realistic photo",
    },

    # ── Целевая аудитория ────────────────────────────────────────────────
    "targetaudience": {
        "prompt_template": (
            "Split composition showing three different people who benefit from {service_en}: "
            "a tired office worker at a desk, an active woman after workout stretching, "
            "a calm middle-aged person reading a book at home, "
            "soft natural daylight, muted warm tones, modern lifestyle aesthetic, "
            "realistic photo, 50mm lens, editorial magazine style, "
            "clean minimal backgrounds"
        ),
        "alt_template": "Кому полезна {service_ru}: офисные работники, спортсмены, люди 30–50 лет",
        "style": "realistic photo",
    },

    # ── FAQ — вопросы и ответы ───────────────────────────────────────────
    "faq": {
        "prompt_template": (
            "Flat lay overhead shot of {service_en} preparation items on a light wooden surface: "
            "small amber glass bottles with essential oils, dried lavender bundles, "
            "a handwritten notebook with a pen, a white ceramic aroma diffuser, "
            "eucalyptus branch, soft even overhead lighting, "
            "realistic product photography, clean organized composition, "
            "unmarked labels, warm natural color palette"
        ),
        "alt_template": "Частые вопросы об услуге {service_ru} в Ноябрьске",
        "style": "realistic photo",
    },

    # ── УТП (уникальное торговое предложение) ────────────────────────────
    "utp": {
        "prompt_template": (
            "A welcoming reception area of a modern health and wellness center, "
            "clean minimalist interior with warm wood accents and green plants, "
            "soft ambient lighting, comfortable seating area, "
            "premium skincare products displayed on a glass shelf, "
            "a small sign reading 'Enthusiast' on the wall, "
            "realistic interior photo, 28mm wide angle lens, f/5.6 aperture, "
            "bright inviting atmosphere, polished surfaces"
        ),
        "alt_template": "Почему выбирают {service_ru} в центре здоровья «Энтузиаст»",
        "style": "realistic photo",
    },
}

# Промпт по умолчанию (fallback, если слот неизвестен)
DEFAULT_SLOT = "process"


# =============================================================================
#  IMAGE_VARIANTS — размеры картинок под каждую площадку
# =============================================================================

IMAGE_VARIANTS: dict[str, list[dict]] = {
    "site": [
        {"variant": "hero",  "width": 1280, "height": 720},
        {"variant": "thumb", "width": 800,  "height": 450},
    ],
    "vk": [
        {"variant": "feed",  "width": 1200, "height": 630},
    ],
    "insta": [
        {"variant": "square", "width": 1080, "height": 1080},
    ],
    "tg": [
        {"variant": "post",  "width": 1280, "height": 720},
    ],
}


# =============================================================================
#  build_prompt_for_slot() — собирает финальный prompt + alt для слота
# =============================================================================

def build_prompt_for_slot(
    slot: str,
    service_ru: str,
    service_en: str,
) -> tuple[str, str, str]:
    """
    Возвращает (prompt, alt, style) для конкретного слота.

    Параметры:
        slot        — имя слота из markdown: problems, mechanism, process, result,
                      targetaudience, faq, utp
        service_ru  — название услуги по-русски:  'ароматерапия'
        service_en  — название услуги по-английски: 'aromatherapy'

    Возвращает:
        (prompt, alt, style)
    """
    slot_key = (slot or "").strip().lower()
    cfg = SLOT_PROMPTS.get(slot_key) or SLOT_PROMPTS[DEFAULT_SLOT]

    prompt = cfg["prompt_template"].format(
        service_en=service_en,
        service_ru=service_ru,
    )
    alt = cfg["alt_template"].format(
        service_en=service_en,
        service_ru=service_ru,
    )
    style = cfg["style"]

    return prompt, alt, style


# =============================================================================
#  build_image_plan_for_slot() — генерирует список вариантов для одного слота
#  (site.hero, site.thumb, vk.feed, insta.square, tg.post)
# =============================================================================

def build_image_plan_for_slot(
    slot: str,
    service_ru: str,
    service_en: str,
    slug: str,
    networks: list[str] | None = None,
) -> list[dict]:
    """
    Для одного слота возвращает список dict-ов (один на каждый variant).

    networks — список сетей, для которых генерируем.
               По умолчанию: ["site", "vk", "insta", "tg"]
    """
    if networks is None:
        networks = list(IMAGE_VARIANTS.keys())

    prompt, alt, style = build_prompt_for_slot(slot, service_ru, service_en)
    items: list[dict] = []

    for network in networks:
        variants = IMAGE_VARIANTS.get(network, [])
        for v in variants:
            items.append({
                "slot":    slot,
                "network": network,
                "variant": v["variant"],
                "width":   v["width"],
                "height":  v["height"],
                "prompt":  prompt,
                "style":   style,
                "alt":     alt,
                "slug":    slug,
            })
    return items


# =============================================================================
#  Пример: Вызов в plan_images_for_post_context()
#  (замена текущего универсального промпта)
# =============================================================================

def plan_images_for_post_context(context: dict) -> dict:
    """
    Основная функция agent8.
    Принимает context (markdown + meta), возвращает plan с images.
    """
    from scripts.shared_config import get_image_protocol

    image_cfg = get_image_protocol()
    meta = context.get("meta", {}) or {}
    serviceslug  = meta.get("serviceslug", "")
    servicename  = meta.get("servicename", "")

    # Маппинг slug → английское название
    # (можно вынести в shared-config или отдельный файл)
    SLUG_TO_EN = {
        "aromaterapiya":   "aromatherapy",
        "pressoterapiya":  "pressotherapy",
        "gidromassazh":    "hydrotherapy massage",
        "karboksiterapiya":"carboxytherapy",
        "massazh":         "relaxation massage",
        "fitoparolechenie":"herbal steam therapy",
        "galoterapiya":    "halotherapy salt room",
        "infrakrasnaya-sauna": "infrared sauna",
    }
    service_en = SLUG_TO_EN.get(serviceslug, serviceslug.replace("-", " "))

    # Парсим markdown, ищем <!-- imageslot XXXX --> комментарии
    md_text = context.get("markdown", "")
    import re
    slots_found = re.findall(r'<!--\s*imageslot\s+(\w+)\s*-->', md_text)

    # Если слоты не найдены, используем дефолтный набор
    if not slots_found:
        slots_found = ["problems", "process", "result", "faq"]

    all_images: list[dict] = []
    for slot in slots_found:
        slot_images = build_image_plan_for_slot(
            slot=slot,
            service_ru=servicename,
            service_en=service_en,
            slug=serviceslug,
            # Можно ограничить: networks=["site"] для начала
        )
        all_images.extend(slot_images)

    return {
        "images": all_images,
        "serviceslug": serviceslug,
    }
