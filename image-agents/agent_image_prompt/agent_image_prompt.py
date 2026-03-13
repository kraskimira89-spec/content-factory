# image-agents/agent_image_prompt — ТЗ на картинки из структуры поста
"""
Принимает структуру поста (title, slug, H2/H3, post_id), вызывает LLM по системному промпту,
возвращает JSON с описанием 1–3 картинок. Сохраняет в output/image_jobs/{post_id}.json.
"""
import json
import os
import sys
from pathlib import Path

# Пути: image-agents/agent_image_prompt/ -> content-factory
_CURRENT = Path(__file__).resolve().parent
_IMAGE_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _IMAGE_AGENTS_DIR.parent
PROMPT_FILE    = PROJECT_ROOT / "prompts" / "agents" / "agent_image_prompt.txt"
PRESETS_FILE   = PROJECT_ROOT / "prompts" / "image_presets.json"
OUTPUT_JOBS_DIR = PROJECT_ROOT / "output" / "image_jobs"

# Подключаем seo-agents/shared (api_client, logger)
_SEO_AGENTS = PROJECT_ROOT / "seo-agents"
if str(_SEO_AGENTS) not in sys.path:
    sys.path.insert(0, str(_SEO_AGENTS))

from shared.api_client import ask_ai  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger("image_agents.prompt")


def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def load_presets() -> dict:
    """Загружает image_presets.json. При отсутствии возвращает пустой dict."""
    if not PRESETS_FILE.exists():
        return {}
    with open(PRESETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_preset_for_service(service_slug: str) -> dict | None:
    """Возвращает пресет по слагу услуги или None."""
    data = load_presets()
    mapping = data.get("service_to_preset", {})
    preset_type = mapping.get(service_slug)
    if not preset_type:
        return None
    for p in data.get("presets", []):
        if p.get("preset_type") == preset_type:
            return p
    return None


def build_user_message(post_struct: dict) -> str:
    """Формирует user-сообщение из структуры поста для LLM."""
    parts = [
        "Структура поста для генерации техзадания на иллюстрации:",
        f"post_id: {post_struct.get('post_id', '')}",
        f"service_slug: {post_struct.get('service_slug', '')}",
        f"title: {post_struct.get('title', '')}",
        f"subtitle: {post_struct.get('subtitle', '')}",
        f"intro: {post_struct.get('intro', '')}",
        "sections (H2/H3):",
        post_struct.get("sections_text", post_struct.get("sections", "")),
    ]
    if post_struct.get("audience"):
        parts.append(f"Целевая аудитория: {post_struct['audience']}")
    if post_struct.get("tone"):
        parts.append(f"Тон: {post_struct['tone']}")

    # Подключаем готовый пресет по слагу услуги
    slug = post_struct.get("service_slug", "")
    preset = get_preset_for_service(slug)
    if preset:
        parts.append("\n--- ПРЕСЕТЫ ---")
        parts.append(f"Рекомендуемый пресет: {preset['preset_type']} ({preset['name']})")
        parts.append(f"Базовый prompt: {preset['prompt']}")
        parts.append(f"Базовый negative_prompt: {preset['negative_prompt']}")
        parts.append(f"Параметры для подстановки (JSON): {json.dumps(preset.get('params', {}), ensure_ascii=False)}")
        parts.append("Адаптируй пресет под услугу и структуру поста.")
    else:
        parts.append("\n(Готового пресета для этого слага нет — составь промпт с нуля по правилам.)")

    return "\n".join(parts)


def generate_image_spec(post_struct: dict) -> dict:
    """
    Вызывает LLM, парсит JSON ответ.
    post_struct: { post_id, service_slug, title, subtitle, intro, sections_text или sections, audience?, tone? }
    Возвращает: { service_slug, post_id, images: [ { id, purpose, prompt, style, aspect_ratio, safety_tags }, ... ] }
    """
    system = load_system_prompt()
    user = build_user_message(post_struct)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    raw = ask_ai(messages, max_tokens=2000)
    # Вырезаем возможный markdown-блок кода
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def save_job(post_id: str, spec: dict) -> Path:
    """Сохраняет JSON в output/image_jobs/{post_id}.json."""
    OUTPUT_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_JOBS_DIR / f"{post_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    logger.info("Сохранён image job: %s", path)
    return path


def run(post_struct: dict) -> dict:
    """
    Точка входа: сгенерировать ТЗ на картинки и сохранить в output/image_jobs.
    post_struct должен содержать post_id, service_slug, title, intro, sections_text (или sections).
    """
    spec = generate_image_spec(post_struct)
    post_id = str(spec.get("post_id", post_struct.get("post_id", "unknown")))
    save_job(post_id, spec)
    return spec


if __name__ == "__main__":
    # Пример: запуск с минимальной структурой
    test_struct = {
        "post_id": "test_001",
        "service_slug": "solyanaya-komnata",
        "title": "Соляная комната в Ноябрьске",
        "subtitle": "Оздоровление дыхания и кожи",
        "intro": "Соляная комната центра «Энтузиаст» — природный микроклимат для всей семьи.",
        "sections_text": "## Что даёт процедура\nУкрепление иммунитета, улучшение дыхания.\n\n## Как проходит сеанс\n40 минут в комфортной атмосфере.",
        "audience": "Семьи, люди с ЛОР-проблемами",
        "tone": "Тёплый, доверительный",
    }
    result = run(test_struct)
    print(json.dumps(result, ensure_ascii=False, indent=2))
