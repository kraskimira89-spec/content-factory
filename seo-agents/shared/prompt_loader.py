"""Загрузка промптов и контекста из prompts/."""
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")


def load_agent_prompt(agent_name: str) -> str:
    """Загружает system prompt агента из prompts/agents/{agent_name}.txt."""
    path = os.path.join(PROMPTS_DIR, "agents", f"{agent_name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_brand_voice() -> str:
    """Загружает brand voice из prompts/context/brand_voice.md."""
    path = os.path.join(PROMPTS_DIR, "context", "brand_voice.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_services_context() -> list[dict]:
    """Загружает список услуг из prompts/context/services.json."""
    path = os.path.join(PROMPTS_DIR, "context", "services.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_service_names() -> list[str]:
    """Возвращает список названий услуг для подсказок."""
    return [s["name"] for s in load_services_context()]
