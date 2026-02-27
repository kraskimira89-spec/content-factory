import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

console = Console()

# Загружаем ключи из .env
load_dotenv(dotenv_path=os.path.join("D:\\content-factory\\config", ".env"))

console.print("\n[bold green]===  ТЕСТ КОНТЕНТ-ЗАВОДА  ===[/bold green]\n")

# Проверка 1: Библиотеки
console.print("[bold]1. Проверка библиотек:[/bold]")
libraries = {
    "openai": False,
    "requests": False,
    "dotenv": False,
    "rich": False,
}

try:
    import openai
    libraries["openai"] = True
except ImportError:
    pass

try:
    import requests
    libraries["requests"] = True
except ImportError:
    pass

try:
    from dotenv import load_dotenv
    libraries["dotenv"] = True
except ImportError:
    pass

try:
    from rich.console import Console
    libraries["rich"] = True
except ImportError:
    pass

table = Table(title="Библиотеки")
table.add_column("Название", style="cyan")
table.add_column("Статус", style="green")

for lib, status in libraries.items():
    emoji = "✅" if status else "❌"
    table.add_row(lib, emoji)

console.print(table)

# Проверка 2: Ключи из .env
console.print("\n[bold]2. Проверка ключей API:[/bold]")
keys = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
    "BASE_URL": os.getenv("BASE_URL"),
    "MODEL_NAME": os.getenv("MODEL_NAME"),
}

key_table = Table(title="Настройки из .env")
key_table.add_column("Параметр", style="cyan")
key_table.add_column("Значение", style="yellow")

for key, value in keys.items():
    display = value if value else "[red]НЕ НАЙДЕН[/red]"
    key_table.add_row(key, display)

console.print(key_table)

# Проверка 3: Папки
console.print("\n[bold]3. Проверка структуры папок:[/bold]")
folders = ["scripts", "prompts", "output", "config"]
for folder in folders:
    path = os.path.join("D:\\content-factory", folder)
    exists = "✅" if os.path.isdir(path) else "❌"
    console.print(f"  {exists} {folder}/")

console.print("\n[bold green]===  ТЕСТ ЗАВЕРШЁН  ===[/bold green]\n")
