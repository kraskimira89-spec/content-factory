"""
Удаление страниц конференц-зала и подстраниц через WP REST API.

Находит страницы по slug: konferenc-zal, korporativnye-treningi, onlajn-shkoly, kouchting
(включая дочерние). Вызывает DELETE для каждой. Учётные данные из config/.env.

Использование:
  python scripts/delete_konferenc_zal_pages.py           # удалить
  python scripts/delete_konferenc_zal_pages.py --dry-run  # только показать
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "config" / ".env")

# Слаги страниц конференц-зала (в т.ч. дочерние)
TARGET_SLUGS = ["konferenc-zal", "korporativnye-treningi", "onlajn-shkoly", "kouchting"]

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0


def _wp_headers(wp_user: str, wp_app_password: str) -> dict:
    """Basic Auth как в agent4_publish."""
    token = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _wp_request(
    method: str,
    url: str,
    wp_user: str,
    wp_app_password: str,
    **kwargs,
) -> requests.Response:
    """HTTP-запрос к WP REST API с retry."""
    headers = _wp_headers(wp_user, wp_app_password)
    kwargs.setdefault("headers", headers)
    kwargs.setdefault("timeout", 30)

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code == 401:
                raise RuntimeError("Авторизация WP не прошла (401). Проверьте WP_USERNAME / WP_APP_PASSWORD")
            if resp.status_code == 403:
                raise RuntimeError("Нет прав (403). Нужна capability delete_pages")
            return resp
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_err = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * attempt
                print(f"  [!] Ошибка (попытка {attempt}/{MAX_RETRIES}), повтор через {wait:.0f} с...")
                time.sleep(wait)

    raise RuntimeError(f"Все {MAX_RETRIES} попыток неудачны: {last_err}")


def find_pages_by_slugs(
    wp_url: str, wp_user: str, wp_app_password: str, slugs: list[str]
) -> list[dict]:
    """Находит все страницы по списку slug (включая с parent)."""
    seen_ids: set[int] = set()
    result: list[dict] = []

    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages"
    params = {"status": "publish,draft,private", "per_page": 100}

    for slug in slugs:
        resp = _wp_request("GET", api_url, wp_user, wp_app_password, params={**params, "slug": slug})
        if resp.status_code != 200:
            print(f"  [!] GET pages?slug={slug}: {resp.status_code}")
            continue

        pages = resp.json()
        for p in pages:
            pid = p.get("id")
            if pid is not None and pid not in seen_ids:
                seen_ids.add(pid)
                result.append({
                    "id": pid,
                    "title": (p.get("title") or {}).get("rendered", ""),
                    "slug": p.get("slug", ""),
                    "link": p.get("link", ""),
                    "parent": p.get("parent", 0),
                })

    # Сортировка: дочерние (parent > 0) первыми, затем родители
    result.sort(key=lambda x: (1 if x["parent"] > 0 else 0, x["id"]))
    return result


def delete_page(
    wp_url: str, wp_user: str, wp_app_password: str, page_id: int
) -> bool:
    """Удаляет страницу. Возвращает True при успехе."""
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages/{page_id}"
    resp = _wp_request("DELETE", url, wp_user, wp_app_password)
    # WP REST API возвращает 200 при успешном удалении (страница в корзину)
    return resp.status_code in (200, 204)


def main(dry_run: bool = False) -> None:
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")

    if not wp_url or not wp_user or not wp_pass:
        print("[ERR] Задайте WP_URL, WP_USERNAME, WP_APP_PASSWORD в config/.env")
        sys.exit(1)

    print("=== Удаление страниц конференц-зала ===")
    print(f"WP_URL: {wp_url}")
    print(f"Слаги: {', '.join(TARGET_SLUGS)}")
    if dry_run:
        print("Режим: --dry-run (без удаления)")
    print()

    pages = find_pages_by_slugs(wp_url, wp_user, wp_pass, TARGET_SLUGS)

    if not pages:
        print("Страницы не найдены.")
        return

    print(f"Найдено страниц: {len(pages)}")
    for p in pages:
        parent_info = f" (parent={p['parent']})" if p["parent"] else ""
        print(f"  • ID={p['id']} slug={p['slug']} «{p['title']}»{parent_info}")
        print(f"    {p['link']}")
    print()

    if dry_run:
        print("--dry-run: удаление не выполняется.")
        return

    deleted: list[dict] = []
    for p in pages:
        try:
            if delete_page(wp_url, wp_user, wp_pass, p["id"]):
                deleted.append(p)
                print(f"[OK] Удалена: ID={p['id']} «{p['title']}» — {p['link']}")
            else:
                print(f"[!] Не удалось удалить ID={p['id']}")
        except Exception as e:
            print(f"[!] Ошибка при удалении ID={p['id']}: {e}")

    print()
    print(f"Удалено страниц: {len(deleted)}")
    for p in deleted:
        print(f"  • {p['link']} (ID={p['id']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Удаление страниц конференц-зала через WP REST API")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать, что будет удалено, без фактического удаления",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
