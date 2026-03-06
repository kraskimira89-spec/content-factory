"""
Запуск цепочки агентов 1→9 для генерации страницы конференц-зала.

Последовательность:
  1. agent1_keywords — ключевые фразы
  2. agent2_brief --konferenc-zal — ТЗ для лендинга
  3. agent3_content --konferenc-zal — текст страницы
  4. agent_editor — редактура (берёт последний файл из output)
  5. scripts/publish_konferenc_zal_from_md.py — конвертация MD→HTML + публикация в WP

Использование:
  python scripts/run_konferenc_zal_chain.py                     # полная цепочка
  python scripts/run_konferenc_zal_chain.py --stop-after 2    # остановиться после агента 2
  python scripts/run_konferenc_zal_chain.py --skip-to 4       # начать с агента 4 (editor)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICE = "Конференц-зал"
CITY = "Ноябрьск"


def run(cmd: list[str], step: str) -> bool:
    """Запускает команду, возвращает True при успехе."""
    print(f"\n{'='*60}\n[{step}]\n{'='*60}")
    r = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if r.returncode != 0:
        print(f"\n[FAIL] {step} завершился с кодом {r.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Цепочка агентов для конференц-зала")
    parser.add_argument("--stop-after", type=int, help="Остановиться после агента N (1-5)")
    parser.add_argument("--skip-to", type=int, default=1, help="Начать с агента N (1-5)")
    args = parser.parse_args()

    steps = [
        (1, "Агент 1 — ключевые фразы", ["python", "seo-agents/agent1_keywords/agent_1_keywords.py", "-s", SERVICE, "-c", CITY]),
        (2, "Агент 2 — ТЗ (конференц-зал)", ["python", "seo-agents/agent2_brief/agent_2_brief.py", "-s", SERVICE, "-c", CITY, "--konferenc-zal"]),
        (3, "Агент 3 — текст страницы (конференц-зал)", ["python", "seo-agents/agent3_content/agent_3_content.py", "--konferenc-zal"]),
        (4, "Агент Editor — редактура", ["python", "seo-agents/agent_editor/agent_editor.py"]),
        (5, "Публикация в WP", ["python", "scripts/publish_konferenc_zal_from_md.py"]),
    ]

    for i, name, cmd in steps:
        if i < args.skip_to:
            continue
        if not run(cmd, name):
            sys.exit(1)
        if args.stop_after and i >= args.stop_after:
            print(f"\nОстановка после агента {i} (--stop-after {args.stop_after})")
            break

    print("\n" + "="*60 + "\nГотово.\n")


if __name__ == "__main__":
    main()
