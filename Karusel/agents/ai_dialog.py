"""
ИИ в диалоге карусели: дополнение краткого ТЗ и генерация примера сценария.
Использует seo-agents/shared/api_client.ask_ai().
"""
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
_PROJECT_ROOT = _KARUSEL_ROOT.parent
_SHARED_DIR = _PROJECT_ROOT / "seo-agents" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from api_client import ask_ai  # type: ignore

sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger

logger = get_logger("ai_dialog")

# Минимальная длина текста, при которой не вызываем дополнение ИИ
BRIEF_MIN_LENGTH = 80

_SYSTEM_EXPAND = """Ты помощник для заполнения ТЗ карусели рекламы услуги.
Пользователь прислал КОРОТКИЙ текст (название услуги, фраза или список).
Твоя задача: дополнить его до ПОЛНОГО ТЗ в 2-4 предложениях без выдумки имён и телефонов.
Включи в ответ (если пользователь не указал):
- название центра (можно общее: "Наш центр", "Студия красоты")
- город (если не указан — напиши "город не указан")
- телефон (заглушка: "+7 (XXX) XXX-XX-XX" или "телефон в описании")
- что входит в услугу / для кого подходит (2-4 коротких пункта)
Пиши только текст ТЗ, без пояснений и без JSON. Язык: русский."""

_SYSTEM_SAMPLE = """Ты помощник для создания примера сценария карусели рекламы услуги.
По подсказке пользователя (одно слово или короткая фраза, например: массаж, углекислая ванна, маникюр)
сгенерируй готовый текст ТЗ для карусели: название центра, город, телефон, кратко что входит и для кого.
Телефон укажи как заглушку: +7 (900) 123-45-67.
Текст должен быть готов к копированию и отправке в бота (2-5 предложений, без markdown и лишних пояснений).
Язык: русский."""


def expand_brief(raw: str) -> str:
    """
    Дополняет короткий текст пользователя до полного ТЗ для парсера карусели.
    Синхронный вызов — в хэндлере вызывать через asyncio.to_thread().
    """
    raw = (raw or "").strip()
    if not raw:
        return raw
    messages = [
        {"role": "system", "content": _SYSTEM_EXPAND},
        {"role": "user", "content": f"Краткий ввод пользователя:\n{raw}"},
    ]
    try:
        response = ask_ai(messages, max_tokens=500)
        out = (response or "").strip()
        logger.info("expand_brief: %d -> %d символов", len(raw), len(out))
        return out if out else raw
    except Exception as e:
        logger.warning("expand_brief ошибка: %s", e)
        return raw


def get_sample_brief(service_hint: str) -> str:
    """
    По подсказке (название услуги) возвращает готовый пример сценария для карусели.
    Синхронный вызов — в хэндлере через asyncio.to_thread().
    """
    hint = (service_hint or "услуга").strip() or "оздоровительная процедура"
    messages = [
        {"role": "system", "content": _SYSTEM_SAMPLE},
        {"role": "user", "content": hint},
    ]
    try:
        response = ask_ai(messages, max_tokens=400)
        out = (response or "").strip()
        logger.info("get_sample_brief: hint=%s, ответ %d символов", hint, len(out))
        return out
    except Exception as e:
        logger.warning("get_sample_brief ошибка: %s", e)
        return (
            f"Услуга: {hint}. Название центра: Наш центр. Город: укажи свой. "
            "Телефон: +7 (900) 123-45-67. Опиши, что входит и для кого подходит."
        )
