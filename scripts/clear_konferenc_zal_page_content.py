"""
Очистка контента страницы конференц-зала, чтобы шаблон показывал статичный макет по Figma.

При пустом content шаблон template-page-landing-konferenc-zal.php выводит
статичный лендинг (Hero с двумя кнопками, 6 карточек мероприятий, преимущества + 2 зала,
«Наш интерьер», «Выгодные предложения», «Доп. услуги», две формы и т.д.).

Использование:
  python scripts/clear_konferenc_zal_page_content.py
  python scripts/clear_konferenc_zal_page_content.py --dry-run
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
load_dotenv(CONFIG_DIR / ".env")


def main():
    parser = argparse.ArgumentParser(description="Очистить контент страницы konferenc-zal для статичного макета")
    parser.add_argument("--dry-run", action="store_true", help="Только показать, что будет сделано")
    args = parser.parse_args()

    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ Задайте WP_URL, WP_USERNAME, WP_APP_PASSWORD в config/.env")
        sys.exit(1)

    token = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    r = requests.get(
        f"{wp_url}/wp-json/wp/v2/pages",
        params={"slug": "konferenc-zal", "status": "publish,draft,private", "per_page": 1},
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200:
        print(f"❌ WP API: {r.status_code}")
        sys.exit(1)

    pages = r.json()
    if not pages:
        print("❌ Страница konferenc-zal не найдена")
        sys.exit(1)

    page_id = pages[0]["id"]
    print(f"Страница konferenc-zal: id={page_id}")

    if args.dry_run:
        print("[dry-run] Будет отправлен PATCH: content='' (пустой контент → статичный макет по Figma)")
        return 0

    resp = requests.post(
        f"{wp_url}/wp-json/wp/v2/pages/{page_id}",
        json={"content": ""},
        headers=headers,
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        print(f"❌ WP API PATCH: {resp.status_code}\n{resp.text[:500]}")
        sys.exit(1)

    print("OK: Content cleared. Static Figma layout is now shown.")
    print(f"   Check: {wp_url}/services/konferenc-zal/")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
