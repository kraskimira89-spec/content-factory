import os
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Текущая папка (agent2_brief)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(CURRENT_DIR, "system_prompt.txt")
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "shared"))

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

from api_client import ask_ai  # type: ignore
from keywords_db import load_keywords  # type: ignore
from logger import get_logger  # type: ignore

console = Console()
logger = get_logger("seo_agents.agent2")

BASE_DIR = r"D:\content-factory"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_system_prompt() -> str:
    """Читаем системный промпт из отдельного файла."""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_brief(service_name: str, city: str, keywords_text: str) -> str:
    prompt = (
        "Ты SEO-копирайтер и контент-стратег.\n"
        "Нужно подготовить ТЗ для SEO-текста (post_content) страницы услуги.\n\n"
        f"Услуга: {service_name}\n"
        f"Город: {city}\n\n"
        "Список ключевых фраз:\n"
        f"{keywords_text}\n\n"
        "ВАЖНО: Шаблон сайта автоматически показывает эти блоки из services_data:\n"
        "- Таблицу цен, FAQ, сравнение с конкурентами, показания/противопоказания,\n"
        "  шаги процедуры, результаты курса.\n"
        "Автор пишет ТОЛЬКО SEO-текст, который идёт в post_content.\n\n"
        "Сделай следующее:\n"
        "1) Предложи H1 (формат: «[Услуга] в [Городе]»).\n"
        "2) Предложи структуру post_content (только то, что пишет автор):\n"
        "   - Лид (эмоциональный крючок, 3-4 предложения)\n"
        "   - H2 «Что даёт [услуга]?» — список выгод\n"
        "   - H2 «Кому особенно нужна?» — целевая аудитория\n"
        "   - H2 «Почему выбирают Центр Энтузиаст?» — преимущества\n"
        "   - Финальный призыв к действию\n"
        "3) Какие преимущества центра «Энтузиаст» выделить в тексте.\n"
        "4) Рекомендации по тону текста (доверительно, экспертно и т.п.).\n"
        "5) Подсказки: какие термины избегать, какие обязательно использовать.\n"
        "6) Напомни автору: НЕ писать цены, FAQ, показания, процедуру — это в шаблоне.\n"
        "Пиши на русском, структурировано, с заголовками и списками."
    )

    system_prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    answer = ask_ai(messages, max_tokens=1500)
    return answer


def save_brief(service_name: str, city: str, brief_text: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_service = service_name.replace(" ", "_")
    safe_city = city.replace(" ", "_")

    filename = f"{timestamp}_brief_{safe_service}_{safe_city}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# ТЗ для страницы: {service_name} — {city}\n\n")
        f.write(brief_text)

    return filepath


def main():
    console.print("\n[bold cyan]Агент 2 — структура страницы и ТЗ[/bold cyan]\n")

    service_name = console.input("Введите [green]название услуги[/green]: ")
    city = console.input("Введите [green]город[/green]: ")
    logger.info("Старт генерации брифа: service=%s, city=%s", service_name, city)

    console.print("\n[dim]Пробую загрузить ключевые фразы из базы...[/dim]\n")
    keywords_text = load_keywords(service_name, city)

    if not keywords_text:
        logger.info(
            "Ключи не найдены в БД для брифа: service=%s, city=%s",
            service_name,
            city,
        )
        console.print(
            "[red]В базе нет ключей для этой услуги и города.[/red]\n"
            "Сначала запусти Агент 1, чтобы сгенерировать ключевые фразы.\n"
        )
        return

    console.print("[bold]Нашёл ключи, генерирую ТЗ...[/bold]\n")

    brief_text = generate_brief(service_name, city, keywords_text)
    logger.info(
        "Бриф сгенерирован: service=%s, city=%s, length=%d",
        service_name,
        city,
        len(brief_text or ""),
    )

    console.print(Panel(brief_text, title="Черновик ТЗ", border_style="green"))

    filepath = save_brief(service_name, city, brief_text)
    logger.info("Бриф сохранён в файл: %s", filepath)

    console.print("\n[bold green]Готово![/bold green]")
    console.print(f"Файл сохранён: [yellow]{filepath}[/yellow]\n")


if __name__ == "__main__":
    main()
