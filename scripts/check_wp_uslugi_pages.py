"""
Проверка страниц Услуги в WordPress.

Для каждого slug из uslugi/services: проверяет существование, длину контента, ссылку.

Использование:
  python scripts/check_wp_uslugi_pages.py
  python scripts/check_wp_uslugi_pages.py --slug uglekislaya-vanna
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
load_dotenv(CONFIG_DIR / ".env")

SHARED_CONFIG = json.loads((CONFIG_DIR / "shared-config.json").read_text("utf-8"))

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USER = os.getenv("WP_USERNAME", "")
WP_PASS = os.getenv("WP_APP_PASSWORD", "")

# Слаги из меню Услуги (порядок как на сайте)
USLUGI_SLUGS = [
    "fitobochka",           # Кедровая бочка
    "solyanaya-komnata",     # Соляная комната
    "pressoterapiya",        # Прессотерапия
    "vlok",                  # ВЛОК
    "sukhaya-uglekislaya-vanna",  # Сухая углекислая ванна
    "uglekislaya-vanna",     # Углекислая ванна (может быть тот же СУВ или отдельная)
    "trenazhernyy-zal",      # Тренажёрный зал
    "massazh",               # Массаж
    "gidromassazh",          # Гидромассаж
    "skrabirovanie",         # Скрабирование
    "obertyvanie",           # Обёртывание
    "nastolnyy-tennis",      # Настольный теннис
    "aromaterapiya",         # Ароматерапия
    "limfodrenazh-nog",      # Лимфодренаж ног
    "nuga-best",             # Нуга Бест
    "fitobar",               # Фитобар
]


def get_page(wp_url: str, wp_user: str, wp_pass: str, slug: str) -> dict | None:
    """Получить страницу по slug через REST API."""
    url = f"{wp_url}/wp-json/wp/v2/pages"
    resp = requests.get(
        url,
        params={"slug": slug, "status": "publish,draft,private", "per_page": 1},
        auth=(wp_user, wp_pass),
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    pages = resp.json()
    if not pages:
        return None
    return pages[0]


def check_pages(slug_filter: str | None = None) -> list[dict]:
    """Проверить страницы. Возвращает список отчётов."""
    if not all([WP_URL, WP_USER, WP_PASS]):
        print("[ERR] WP_URL, WP_USERNAME, WP_APP_PASSWORD не заданы в config/.env")
        sys.exit(1)

    slugs = [s for s in USLUGI_SLUGS if not slug_filter or s == slug_filter]
    if not slugs and slug_filter:
        slugs = [slug_filter]

    results = []
    for slug in slugs:
        page = get_page(WP_URL, WP_USER, WP_PASS, slug)
        if not page:
            results.append({"slug": slug, "status": "404", "link": "", "content_len": 0})
            continue

        content = page.get("content", {}).get("rendered", "") or page.get("content", "")
        if isinstance(content, dict):
            content = content.get("rendered", "")
        content_stripped = content.replace("<", " ").replace(">", " ")  # грубая длина текста
        clen = len(content_stripped)

        status = "OK" if clen > 200 else "EMPTY" if clen < 50 else "SHORT"
        results.append({
            "slug": slug,
            "status": status,
            "link": page.get("link", ""),
            "content_len": clen,
            "page_id": page.get("id"),
        })

    return results


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="Проверить только один slug")
    args = ap.parse_args()

    results = check_pages(args.slug)
    print(f"WP: {WP_URL}")
    print("-" * 70)
    for r in results:
        status_icon = "[OK]" if r["status"] == "OK" else "[!!]" if r["status"] == "EMPTY" else "[~]"
        print(f"{status_icon} {r['slug']:28} {r['status']:6} len={r['content_len']:5} {r['link']}")

    empty = [r["slug"] for r in results if r["status"] == "EMPTY"]
    if empty:
        print(f"\nПустые страницы ({len(empty)}): {', '.join(empty)}")
        print("Заполнить: python seo-agents/agent4_publish/agent_4_publish.py <slug>")


if __name__ == "__main__":
    main()
