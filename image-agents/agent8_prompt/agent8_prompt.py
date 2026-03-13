# image-agents/agent8_prompt — генератор промптов для картинок (agent8_images_planner)
"""
На вход: готовый текст поста + метаданные (ниша, тип услуги, тон, ключевые смыслы).
На выход: JSON по image_protocol: images: [{ prompt, negative_prompt, style, alt }, ...].

Автоматически подбирает пресет из prompts/image_presets.json по service_type,
подставляет параметры из metadata.params (или дефолтные значения).
"""
import json
import re
import sys
from pathlib import Path

_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent
PROMPT_FILE   = PROJECT_ROOT / "prompts" / "agent_images_system.txt"
PRESETS_FILE  = PROJECT_ROOT / "prompts" / "image_presets.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "seo-agents") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "seo-agents"))
from scripts.shared_config import get_image_protocol  # noqa: E402
from shared.api_client import ask_ai  # noqa: E402


# ─── Пресеты ────────────────────────────────────────────────────────────────

def load_presets() -> dict:
    """Загружает image_presets.json. При отсутствии — пустой dict."""
    if not PRESETS_FILE.exists():
        return {}
    with open(PRESETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_preset(service_slug: str) -> dict | None:
    """
    Возвращает пресет по слагу услуги (через service_to_preset → id).
    Если слаг не найден — возвращает None.
    """
    data = load_presets()
    preset_id = data.get("service_to_preset", {}).get(service_slug)
    if not preset_id:
        return None
    for p in data.get("image_presets", []):
        if p.get("id") == preset_id:
            return p
    return None


def apply_params(template: str, params_spec: dict, overrides: dict) -> str:
    """
    Подставляет значения параметров в строку-шаблон вида {param_name}.
    overrides берёт значения из metadata.params; если нет — берёт default из params_spec.
    """
    values = {}
    for key, spec in params_spec.items():
        values[key] = overrides.get(key, spec.get("default", ""))
    # Заменяем плейсхолдеры; пустые значения убираем вместе с запятой/пробелом
    result = template
    for key, val in values.items():
        placeholder = "{" + key + "}"
        if val:
            result = result.replace(placeholder, val)
        else:
            # Убираем пустой тег вместе с окружающей запятой и пробелами
            result = re.sub(r",?\s*" + re.escape(placeholder) + r"\s*,?", ",", result)
    # Чистим двойные запятые и пробелы
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r"^,\s*|,\s*$", "", result.strip())
    return result


def build_preset_block(service_slug: str, param_overrides: dict) -> str:
    """
    Формирует текстовый блок «ПРЕСЕТ» для передачи агенту.
    Возвращает пустую строку, если пресет не найден.
    """
    preset = get_preset(service_slug)
    if not preset:
        return ""

    params_spec = preset.get("params", {})
    prompt = apply_params(preset["base_prompt"], params_spec, param_overrides)
    neg    = preset["base_negative_prompt"]

    lines = [
        "--- ПРЕСЕТ ---",
        f"preset_id:       {preset['id']}",
        f"title:           {preset['title']}",
        f"service_type:    {preset['service_type']}",
        f"aspect_ratio:    {preset.get('aspect_ratio', '16:9')}",
        f"style:           {preset.get('style', '')}",
        f"base_prompt:     {prompt}",
        f"base_negative:   {neg}",
        "",
        "Используй base_prompt как основу. Дополни 2–3 тегами из текста поста.",
        "negative_prompt бери из base_negative без изменений (можно дополнить).",
        "В JSON-ответе добавь поле preset_id.",
    ]
    return "\n".join(lines)


# ─── Основная логика ─────────────────────────────────────────────────────────

def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def build_user_message(post_text: str, metadata: dict) -> str:
    """Текст поста + метаданные + подобранный пресет."""
    proto = get_image_protocol()
    count = proto.get("count") or {}
    min_count = count.get("min", 1)
    max_count = count.get("max", 3)

    service_slug   = metadata.get("service_slug", metadata.get("service_type", ""))
    param_overrides = metadata.get("params", {})
    preset_block   = build_preset_block(service_slug, param_overrides)

    meta_clean = {k: v for k, v in metadata.items() if k != "params"}
    meta_str   = json.dumps(meta_clean, ensure_ascii=False, indent=2)

    parts = [
        "Текст поста:",
        "",
        post_text,
        "",
        "---",
        "",
        "Метаданные (JSON):",
        "",
        meta_str,
    ]

    if preset_block:
        parts += ["", preset_block]
    else:
        parts.append("\n(Готового пресета нет — составь промпт с нуля по правилам.)")

    parts += [
        "",
        f"Сгенерируй от {min_count} до {max_count} промптов для Stable Diffusion в формате JSON.",
        'Поле "images" — массив объектов с полями:',
        '  "prompt"          — теги через запятую (английский, 10–20 тегов),',
        '  "negative_prompt" — теги-запреты (английский),',
        '  "style"           — краткое описание стиля,',
        '  "alt"             — alt-текст для сайта (русский),',
        '  "preset_id"       — id использованного пресета или "custom".',
        "ВАЖНО: prompt — только теги через запятую, НЕ предложения.",
    ]

    return "\n".join(parts)


def run(post_text: str, metadata: dict) -> dict:
    """
    Возвращает: { "images": [...], "style": "...", "safety_notes": "..." }.
    metadata может содержать:
      service_slug / service_type — слаг услуги для выбора пресета
      params — dict с override-значениями параметров пресета
    """
    system = load_system_prompt()
    user   = build_user_message(post_text, metadata)
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    raw = ask_ai(messages, max_tokens=2000)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Агент 8: генерация промптов для картинок")
    parser.add_argument("--text",  type=str, help="Путь к .md или текст поста")
    parser.add_argument("--meta",  type=str, default="{}", help="JSON метаданных")
    parser.add_argument("--slug",  type=str, default="",   help="Слаг услуги (для выбора пресета)")
    parser.add_argument("--params",type=str, default="{}",  help="JSON параметров пресета")
    args = parser.parse_args()

    if args.text and Path(args.text).is_file():
        post_text = Path(args.text).read_text(encoding="utf-8")
    else:
        post_text = args.text or "Пример текста поста о прессотерапии."

    meta = json.loads(args.meta)
    if args.slug:
        meta["service_slug"] = args.slug
    if args.params != "{}":
        meta["params"] = json.loads(args.params)

    result = run(post_text, meta)
    print(json.dumps(result, ensure_ascii=False, indent=2))
