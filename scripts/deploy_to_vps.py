"""
Деплой service-pages-defaults-patch-generated.php на VPS.

Два режима:
  --mode ssh   : копирует PHP-файл по SSH (SCP) и перезаписывает на сервере
  --mode rest  : отправляет JSON-данные через кастомный REST-эндпоинт WP

Использование:
  python scripts/deploy_to_vps.py --mode ssh
  python scripts/deploy_to_vps.py --mode rest
"""
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"

load_dotenv(CONFIG_DIR / ".env")

SHARED_CONFIG = json.loads((CONFIG_DIR / "shared-config.json").read_text("utf-8"))


def deploy_ssh():
    """Копирует сгенерированный PHP-патч на VPS через SCP."""
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


def deploy_rest():
    """
    Отправляет данные услуг через кастомный REST-эндпоинт WordPress.
    Требует плагин/mu-plugin на стороне WP, принимающий POST /wp-json/cf/v1/options.
    """
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_password = os.getenv("WP_APP_PASSWORD", "")

    if not all([wp_url, wp_user, wp_password]):
        print("❌ WP_URL / WP_USERNAME / WP_APP_PASSWORD не заданы в config/.env")
        sys.exit(1)

    json_file = OUTPUT_DIR / "services-patch-data.json"
    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        print("   Сначала запустите: python scripts/deploy_services_data.py")
        sys.exit(1)

    data = json.loads(json_file.read_text("utf-8"))

    endpoint = f"{wp_url}{SHARED_CONFIG['endpoints']['options']['path']}"
    credentials = f"{wp_user}:{wp_password}"
    token = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {token}",
    }

    import requests
    print(f"📤 REST: POST {endpoint}")
    print(f"   Услуг в патче: {len(data)}")

    resp = requests.post(endpoint, json=data, headers=headers, timeout=30)

    if resp.status_code in (200, 201):
        print(f"✅ Данные приняты сервером ({resp.status_code})")
        body = resp.json()
        if "updated" in body:
            print(f"   Обновлено услуг: {body['updated']}")
    else:
        print(f"❌ Ошибка ({resp.status_code}):")
        print(resp.text[:500])
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Деплой service data на VPS")
    parser.add_argument(
        "--mode",
        choices=["ssh", "rest"],
        default="ssh",
        help="Способ доставки: ssh (SCP) или rest (WP REST API)",
    )
    args = parser.parse_args()

    print(f"=== Деплой на VPS (режим: {args.mode}) ===\n")

    if args.mode == "ssh":
        deploy_ssh()
    else:
        deploy_rest()


if __name__ == "__main__":
    main()
