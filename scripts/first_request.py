import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

console = Console()

# Загружаем настройки
load_dotenv(dotenv_path="D:\\content-factory\\config\\.env")

api_key = os.getenv("PERPLEXITY_API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv("MODEL_NAME")

console.print("\n[bold cyan]🏭 КОНТЕНТ-ЗАВОД — Первый запрос[/bold cyan]\n")
console.print(f"Модель: [yellow]{model}[/yellow]")
console.print(f"Сервер: [yellow]{base_url}[/yellow]")
console.print("[dim]Отправляю запрос... подожди 10-20 секунд...[/dim]\n")

# Подключаемся к API
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# Отправляем запрос
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "Ты — помощник контент-завода. Отвечай кратко и по делу на русском языке."
        },
        {
            "role": "user",
            "content": "Напиши 3 идеи для статей про здоровый образ жизни. Кратко, по одному предложению на каждую идею."
        }
    ],
    max_tokens=500,
)

# Показываем ответ
answer = response.choices[0].message.content

console.print(Panel(
    answer,
    title="[bold green]Ответ AI[/bold green]",
    border_style="green",
    padding=(1, 2),
))

console.print("\n[bold green]✅ Контент-завод работает! Первый запрос выполнен![/bold green]\n")
