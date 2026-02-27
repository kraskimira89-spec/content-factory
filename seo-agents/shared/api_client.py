import os
from dotenv import load_dotenv
from openai import OpenAI

from logger import get_logger

# Базовая папка проекта
BASE_DIR = r"D:\content-factory"

# Путь к .env
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")

# Загружаем переменные окружения
load_dotenv(ENV_PATH)

API_KEY = os.getenv("PERPLEXITY_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "sonar-pro")

logger = get_logger("seo_agents.api_client")

if not API_KEY:
    logger.error("PERPLEXITY_API_KEY не найден в .env")
    raise RuntimeError("PERPLEXITY_API_KEY не найден в .env")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

def ask_ai(messages, model: str | None = None, **kwargs) -> str:
    """
    Универсальная функция для запросов к AI.
    messages — список сообщений формата OpenAI.
    Возвращает текст первого ответа.
    """
    if model is None:
        model = MODEL_NAME

    logger.info(
        "ask_ai: model=%s, messages=%d, max_tokens=%s",
        model,
        len(messages),
        kwargs.get("max_tokens"),
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs,
    )

    content = response.choices[0].message.content
    logger.info("ask_ai: got response (%d chars)", len(content or ""))
    return content


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
