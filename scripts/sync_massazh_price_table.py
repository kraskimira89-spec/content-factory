"""
Одноразовая синхронизация таблицы цен массажа в БД WordPress.

Читает output/massazh-price-table.json и отправляет в wp_options через
POST /wp-json/entuziastov75/v1/service-data/massazh (merge с существующими данными).

Запуск из корня проекта:
  python scripts/sync_massazh_price_table.py
  python scripts/sync_massazh_price_table.py --dry-run
"""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"

load_dotenv(CONFIG_DIR / ".env")
SHARED_CONFIG = json.loads((CONFIG_DIR / "shared-config.json").read_text("utf-8"))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Записать таблицу цен массажа в БД (service_extra_massazh)")
    parser.add_argument("--dry-run", action="store_true", help="Не отправлять запрос")
    args = parser.parse_args()

    json_path = OUTPUT_DIR / "massazh-price-table.json"
    if not json_path.exists():
        print(f"ERR: Файл не найден: {json_path}")
        sys.exit(1)

    price_table = json.loads(json_path.read_text("utf-8"))
    if not isinstance(price_table, list) or not price_table:
        print("ERR: Ожидается непустой массив объектов в JSON")
        sys.exit(1)

    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_password = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_password]):
        print("ERR: WP_URL / WP_USERNAME / WP_APP_PASSWORD не заданы в config/.env")
        sys.exit(1)

    endpoint_tpl = SHARED_CONFIG["endpoints"]["service_data"]["path"]
    url = f"{wp_url}{endpoint_tpl.replace('{slug}', 'massazh')}"
    body = {"price_table": price_table}

    print(f"Таблица цен массажа: {len(price_table)} строк -> {url}")
    if args.dry_run:
        print("   (dry-run — запрос не отправляется)")
        return

    try:
        resp = requests.post(url, json=body, auth=(wp_user, wp_password), timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            print(f"   OK {resp.status_code}, обновлены ключи: {data.get('updated_keys', [])}")
        else:
            print(f"   ERR {resp.status_code}: {resp.text[:300]}")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"   ERR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
