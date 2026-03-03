import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError

from logger import get_logger

# Базовая папка проекта
BASE_DIR = r"D:\content-factory"

# Путь к .env
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")

# Загружаем переменные окружения
load_dotenv(ENV_PATH)

logger = get_logger("seo_agents.api_client")

# Список запасных API: (api_key_env, base_url_env, model_env/default)
# При сбое (401, 429, соединение) пробуем следующий
_API_BACKENDS = [
    ("PERPLEXITY_API_KEY", "BASE_URL", "MODEL_NAME"),
    ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"),
]
_DEFAULT_MODELS = ["sonar-pro", "gpt-4o-mini"]


def _get_clients():
    """Возвращает список (client, model) для fallback."""
    result = []
    for i, (key_env, url_env, model_env) in enumerate(_API_BACKENDS):
        api_key = os.getenv(key_env, "").strip()
        base_url = os.getenv(url_env, "").strip()
        model = os.getenv(model_env, "").strip() or (_DEFAULT_MODELS[i] if i < len(_DEFAULT_MODELS) else "gpt-4o-mini")
        if api_key and base_url:
            result.append((OpenAI(api_key=api_key, base_url=base_url), model))
    return result


def ask_ai(messages, model: str | None = None, **kwargs) -> str:
    """
    Универсальная функция для запросов к AI.
    При сбое (401, 429, соединение) пробует запасные API из .env.
    """
    clients = _get_clients()
    if not clients:
        raise RuntimeError(
            "Нет доступных API. Добавьте PERPLEXITY_API_KEY+BASE_URL или "
            "OPENAI_API_KEY+OPENAI_BASE_URL в config/.env"
        )

    last_error = None
    for idx, (client, backend_model) in enumerate(clients):
        use_model = model or backend_model
        try:
            logger.info(
                "ask_ai: backend=%d, model=%s, messages=%d",
                idx + 1, use_model, len(messages),
            )
            response = client.chat.completions.create(
                model=use_model,
                messages=messages,
                **kwargs,
            )
            content = response.choices[0].message.content
            logger.info("ask_ai: got response (%d chars) from backend %d", len(content or ""), idx + 1)
            return content
        except (AuthenticationError, RateLimitError, APIConnectionError, APIError) as e:
            last_error = e
            logger.warning("ask_ai: backend %d failed (%s), trying next...", idx + 1, type(e).__name__)
            continue

    raise RuntimeError(f"Все API недоступны. Последняя ошибка: {last_error}") from last_error


if __name__ == "__main__":
    # Небольшой самотест
    logger.info("Запуск самотеста api_client")
    test_messages = [
        {
            "role": "system",
            "content": "Ты — помощник контент-завода. Отвечай кратко на русском.",
        },
        {
            "role": "user",
            "content": "Скажи одной фразой: 'Я готов работать для контент-завода Сергея'.",
        },
    ]

    print("Отправляю тестовый запрос через shared.api_client...\n")
    answer = ask_ai(test_messages, max_tokens=100)
    print("Ответ AI:\n")
    print(answer)
