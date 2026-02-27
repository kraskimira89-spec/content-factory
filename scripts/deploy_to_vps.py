"""
Деплой данных услуг на VPS.

Два режима:
  --mode rest  : отправляет JSON по REST API (POST /wp-json/entuziastov75/v1/service-data/{slug})
  --mode ssh   : копирует PHP-файл по SSH (SCP) — фоллбэк

Опции:
  --slug NAME  : деплоить только одну услугу (по умолчанию — все из services-patch-data.json)
  --dry-run    : показать что будет отправлено, без реального запроса

Использование:
  python scripts/deploy_to_vps.py --mode rest
  python scripts/deploy_to_vps.py --mode rest --slug solyanaya-komnata
  python scripts/deploy_to_vps.py --mode rest --dry-run
  python scripts/deploy_to_vps.py --mode ssh
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"

load_dotenv(CONFIG_DIR / ".env")

SHARED_CONFIG = json.loads((CONFIG_DIR / "shared-config.json").read_text("utf-8"))


def _wp_auth():
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_password = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_password]):
        print("❌ WP_URL / WP_USERNAME / WP_APP_PASSWORD не заданы в config/.env")
        sys.exit(1)
    return wp_url, (wp_user, wp_password)


def _load_patch_data() -> dict:
    json_file = OUTPUT_DIR / "services-patch-data.json"
    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        print("   Сначала запустите: python scripts/deploy_services_data.py")
        sys.exit(1)
    return json.loads(json_file.read_text("utf-8"))


def deploy_rest(slug_filter: str | None = None, dry_run: bool = False):
    """
    POST данных каждой услуги на /wp-json/entuziastov75/v1/service-data/{slug}.
    Эндпоинт мержит данные с дефолтами из PHP, фильтрует чужие ключи.
    """
    wp_url, auth = _wp_auth()
    data = _load_patch_data()

    endpoint_tpl = SHARED_CONFIG["endpoints"]["service_data"]["path"]

    if slug_filter:
        if slug_filter not in data:
            print(f"❌ Slug '{slug_filter}' не найден в services-patch-data.json")
            print(f"   Доступные: {', '.join(data.keys())}")
            sys.exit(1)
        data = {slug_filter: data[slug_filter]}

    print(f"📤 REST-деплой: {len(data)} услуг(а) → {wp_url}")
    if dry_run:
        print("   (dry-run — запросы не отправляются)\n")

    ok, fail = 0, 0
    for slug, fields in data.items():
        url = f"{wp_url}{endpoint_tpl.replace('{slug}', slug)}"
        keys_list = ", ".join(fields.keys())
        print(f"  → {slug}: {keys_list}")

        if dry_run:
            ok += 1
            continue

        try:
            resp = requests.post(url, json=fields, auth=auth, timeout=30)
            if resp.status_code in (200, 201):
                print(f"    ✅ {resp.status_code}")
                ok += 1
            else:
                print(f"    ❌ {resp.status_code}: {resp.text[:200]}")
                fail += 1
        except requests.RequestException as e:
            print(f"    ❌ Ошибка соединения: {e}")
            fail += 1

    print(f"\n{'Dry-run завершён' if dry_run else 'Готово'}: ✅ {ok}  ❌ {fail}")
    if fail:
        sys.exit(1)


def deploy_ssh():
    """Копирует сгенерированный PHP-патч на VPS через SCP (фоллбэк)."""
    host = os.getenv("VPS_HOST", "").strip()
    user = os.getenv("VPS_USER", "root").strip()
    key_path = os.getenv("VPS_SSH_KEY", "").strip()

    if not host:
        print("❌ VPS_HOST не задан в config/.env")
        print("   Добавьте: VPS_HOST=91.229.11.147")
        sys.exit(1)

    local_file = OUTPUT_DIR / "service-pages-defaults-patch-generated.php"
    if not local_file.exists():
        print(f"❌ Файл не найден: {local_file}")
        print("   Сначала запустите: python scripts/deploy_services_data.py")
        sys.exit(1)

    remote_path = SHARED_CONFIG["deploy"]["theme_path"]

    scp_cmd = ["scp"]
    if key_path:
        scp_cmd += ["-i", key_path]
    scp_cmd += [str(local_file), f"{user}@{host}:{remote_path}"]

    print(f"📤 SCP: {local_file.name} → {user}@{host}:{remote_path}")
    result = subprocess.run(scp_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Файл успешно скопирован на VPS")
    else:
        print(f"❌ Ошибка SCP (код {result.returncode}):")
        print(result.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Деплой service data на VPS")
    parser.add_argument(
        "--mode", choices=["rest", "ssh"], default="rest",
        help="Способ доставки: rest (WP REST API) или ssh (SCP-фоллбэк)",
    )
    parser.add_argument(
        "--slug", default=None,
        help="Деплоить только одну услугу (slug из services-patch-data.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Показать что будет отправлено, без реального запроса",
    )
    args = parser.parse_args()

    print(f"=== Деплой на VPS (режим: {args.mode}) ===\n")

    if args.mode == "rest":
        deploy_rest(slug_filter=args.slug, dry_run=args.dry_run)
    else:
        deploy_ssh()


if __name__ == "__main__":
    main()
