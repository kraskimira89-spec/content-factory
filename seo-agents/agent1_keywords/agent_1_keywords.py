import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Текущая папка (agent1_keywords)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(CURRENT_DIR, "system_prompt.txt")

# Путь к shared (..\shared)
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))

# Добавляем shared в sys.path
if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

# Теперь можно импортировать api_client напрямую
from api_client import ask_ai  # type: ignore
from keywords_db import save_keywords as db_save_keywords  # type: ignore
from db_session import set_last_pair  # type: ignore
from logger import get_logger  # type: ignore

console = Console()
logger = get_logger("seo_agents.agent1")

# Базовая папка проекта и output
BASE_DIR = r"D:\content-factory"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_system_prompt() -> str:
    """Читаем системный промпт из отдельного файла."""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_keywords(service_name: str, city: str) -> str:
    """Запрашивает у AI список ключевых фраз под услугу и город."""
    prompt = (
        "Ты SEO-специалист. Составь список ключевых фраз для страницы услуги.\n"
        f"Услуга: {service_name}\n"
        f"Город: {city}\n\n"
        "Требования:\n"
        "1) Пиши на русском.\n"
        "2) Сначала 5–7 основных высокочастотных ключей.\n"
        "3) Затем 10–15 дополнительных (средне- и низкочастотных).\n"
        "4) Выводи в виде простого списка, по одному ключу в строке, без пояснений.\n"
    )

    system_prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    answer = ask_ai(messages, max_tokens=800)
    return answer


def save_keywords(service_name: str, city: str, keywords_text: str) -> str:
    """Сохраняет ключевые фразы в файл в папке output."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_service = service_name.replace(" ", "_")
    safe_city = city.replace(" ", "_")

    filename = f"{timestamp}_keywords_{safe_service}_{safe_city}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Услуга: {service_name}\n")
        f.write(f"Город: {city}\n\n")
        f.write("Ключевые фразы:\n\n")
        f.write(keywords_text)

    return filepath


def main():
    console.print("\n[bold cyan]Агент 1 — генератор ключевых фраз[/bold cyan]\n")

    service_name = console.input("Введите [green]название услуги[/green]: ")
    city = console.input("Введите [green]город[/green]: ")
    logger.info("Старт запроса ключей: service=%s, city=%s", service_name, city)

    console.print("\n[dim]Отправляю запрос к AI, подождите...[/dim]\n")

    keywords_text = generate_keywords(service_name, city)
    logger.info(
        "Ключи сгенерированы: service=%s, city=%s, length=%d",
        service_name,
        city,
        len(keywords_text or ""),
    )

    console.print("\n[bold]Черновик ключевых фраз:[/bold]\n")
    console.print(keywords_text)

    # Сохраняем в базу
    db_save_keywords(service_name, city, keywords_text)
    set_last_pair(service_name, city)
    logger.info("Ключи сохранены в БД и отмечены как последние: %s — %s", service_name, city)

    filepath = save_keywords(service_name, city, keywords_text)
    logger.info("Ключи сохранены в файл: %s", filepath)

    console.print("\n[bold green]Готово![/bold green]")
    console.print(f"Файл сохранён: [yellow]{filepath}[/yellow]\n")


if __name__ == "__main__":
    main()
