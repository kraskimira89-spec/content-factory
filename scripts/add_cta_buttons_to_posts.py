"""
Добавляет кнопки, стили заголовков, жирные ключи и перелинковку в посты блога.

Использование:
  python scripts/add_cta_buttons_to_posts.py           # обновить все посты
  python scripts/add_cta_buttons_to_posts.py --dry-run # показать, что будет сделано
"""
import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "config" / ".env")
_CONFIG = json.loads((PROJECT_ROOT / "config" / "shared-config.json").read_text("utf-8"))

WP_URL = (os.getenv("WP_URL") or "").rstrip("/")
WP_USER = os.getenv("WP_USERNAME", "")
WP_PASS = os.getenv("WP_APP_PASSWORD", "")

CTA_BUTTONS_MARKER = "background: #24937a"  # маркер кнопок
BLOG_HEADING_COLOR = "#24937a"


def _auth_headers():
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def _has_cta_buttons(content: str) -> bool:
    """Проверяет, есть ли уже блок кнопок в контенте."""
    return CTA_BUTTONS_MARKER in content and "Записаться" in content


def apply_blog_heading_styles(html: str) -> str:
    """Зелёный цвет заголовков, H1→H2 (заголовок поста уже H1)."""
    html = re.sub(r"<h1(\s[^>]*)?>", r"<h2\1>", html, flags=re.IGNORECASE)
    html = re.sub(r"</h1>", "</h2>", html, flags=re.IGNORECASE)

    def add_color(match: re.Match) -> str:
        tag = match.group(0)
        if "style=" in tag and "color:" not in tag:
            return re.sub(
                r'(style=["\'])([^"\']*?)(["\'])',
                rf"\1\2; color: {BLOG_HEADING_COLOR}; font-family: sans-serif\3",
                tag,
                count=1,
            )
        if "style=" in tag and "font-family:" not in tag:
            return re.sub(r'(style=["\'])([^"\']*?)(["\'])', r"\1\2; font-family: sans-serif\3", tag, count=1)
        if "style=" in tag:
            return tag
        return tag[:-1] + f' style="color: {BLOG_HEADING_COLOR}; font-family: sans-serif">'

    for tag_name in ["h2", "h3", "h4", "h5", "h6"]:
        html = re.sub(rf"<{tag_name}(\s[^>]*)?>", add_color, html)
    return html


def _build_service_phrase_map() -> list[tuple[str, str]]:
    """(phrase, slug) из services, длинные фразы первыми."""
    phrases = []
    for slug, data in _CONFIG.get("services", {}).items():
        name = data.get("name", "")
        aliases = data.get("aliases") or []
        for p in [name] + list(aliases):
            if p and str(p).strip():
                phrases.append((str(p).strip(), slug))
    phrases.sort(key=lambda x: -len(x[0]))
    return phrases


def apply_blog_keywords_and_links(html: str, base_url: str) -> str:
    """Жирные ключи + перелинковка на страницы услуг."""
    phrase_map = _build_service_phrase_map()
    if not phrase_map:
        return html
    parts = re.split(r"(<[^>]+>)", html)
    linked: set[str] = set()
    result = []
    for part in parts:
        if part.startswith("<"):
            result.append(part)
            continue
        text = part
        for phrase, slug in phrase_map:
            if phrase.lower() not in text.lower():
                continue
            if phrase in linked:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                text = pattern.sub(lambda m: f"<strong>{m.group(0)}</strong>", text)
            else:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                link = f'<a href="{base_url}/uslugi/{slug}/"><strong>\\g<0></strong></a>'
                text = pattern.sub(link, text, count=1)
                linked.add(phrase)
        result.append(text)
    return "".join(result)


def _build_cta_buttons(base_url: str) -> str:
    """Формирует HTML-блок кнопок."""
    return (
        '\n<p style="margin-top: 2em; display: flex; gap: 1em; flex-wrap: wrap;">'
        f'<a href="{base_url}/blog/" style="display: inline-block; padding: 0.6em 1.2em; '
        'background: #24937a; color: #fff; text-decoration: none; border-radius: 4px; border: 1px solid #1a6b5a;">Далее</a>'
        f'<a href="{base_url}/#callback" style="display: inline-block; padding: 0.6em 1.2em; '
        'background: #ff8800; color: #fff; text-decoration: none; border-radius: 4px;">Записаться</a>'
        '</p>'
    )


def fetch_published_posts() -> list[dict]:
    """Получает все опубликованные посты."""
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    posts = []
    page = 1
    while True:
        resp = requests.get(
            url,
            params={"status": "publish", "per_page": 100, "page": page},
            headers=_auth_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"Ошибка GET: {resp.status_code} {resp.text[:200]}")
            return []
        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def update_post(post_id: int, content: str, dry_run: bool) -> bool:
    """Обновляет контент поста."""
    if dry_run:
        return True
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    resp = requests.post(
        url,
        json={"content": content},
        headers=_auth_headers(),
        timeout=30,
    )
    return resp.status_code in (200, 201)


def main():
    parser = argparse.ArgumentParser(description="Добавить кнопки Далее/Записаться в опубликованные посты")
    parser.add_argument("--dry-run", action="store_true", help="Не вносить изменения, только показать")
    args = parser.parse_args()

    if not all([WP_URL, WP_USER, WP_PASS]):
        print("Ошибка: задайте WP_URL, WP_USERNAME, WP_APP_PASSWORD в config/.env")
        sys.exit(1)

    print(f"WP_URL: {WP_URL}")
    print(f"Режим: {'dry-run (без изменений)' if args.dry_run else 'обновление постов'}\n")

    posts = fetch_published_posts()
    print(f"Найдено опубликованных постов: {len(posts)}")

    cta_html = _build_cta_buttons(WP_URL)
    updated = 0
    skipped = 0

    for p in posts:
        post_id = p["id"]
        title = p.get("title", {})
        if isinstance(title, dict):
            title = title.get("rendered", str(post_id))
        else:
            title = str(post_id)
        raw_content = p.get("content")
        if isinstance(raw_content, dict):
            content = raw_content.get("raw", "") or raw_content.get("rendered", "")
        else:
            content = str(raw_content or "")

        if not content or not content.strip():
            skipped += 1
            continue

        new_content = apply_blog_heading_styles(content)
        new_content = apply_blog_keywords_and_links(new_content, WP_URL)
        if not _has_cta_buttons(new_content):
            new_content = (new_content.rstrip() + cta_html).strip()

        if new_content == content:
            skipped += 1
            continue

        if update_post(post_id, new_content, args.dry_run):
            updated += 1
            print(f"  {'[dry-run] ' if args.dry_run else ''}ID={post_id}: {title[:50]}...")

    print(f"\nГотово: обновлено {updated}, пропущено {skipped}")


if __name__ == "__main__":
    main()
