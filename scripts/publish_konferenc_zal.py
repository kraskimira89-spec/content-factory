"""
Публикация JSON‑лендингов конференц‑зала в WordPress.

Читает JSON из docs/, конвертирует в HTML, создаёт или обновляет страницу через REST API.

Использование:
  python scripts/publish_konferenc_zal.py                      # все 3 страницы
  python scripts/publish_konferenc_zal.py korporativnye-treningi  # одна
  python scripts/publish_konferenc_zal.py --dry-run           # без отправки
  python scripts/publish_konferenc_zal.py --output-html       # только сгенерировать HTML в output/

План: docs/konferenc-zal-wp-integration-plan.md
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR = PROJECT_ROOT / "output"

load_dotenv(CONFIG_DIR / ".env")
SHARED_CONFIG = json.loads((CONFIG_DIR / "shared-config.json").read_text("utf-8"))


def _wp_auth() -> tuple[str, str, str]:
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_pass]):
        raise RuntimeError("WP_URL / WP_USERNAME / WP_APP_PASSWORD не заданы в config/.env")
    return wp_url, wp_user, wp_pass


def _wp_headers(wp_user: str, wp_pass: str, json_content: bool = True) -> dict:
    token = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    h = {"Authorization": f"Basic {token}"}
    if json_content:
        h["Content-Type"] = "application/json"
    return h


def find_page(wp_url: str, wp_user: str, wp_pass: str, slug: str) -> dict | None:
    """Ищет страницу по slug. Возвращает dict с id, title, link или None."""
    url = f"{wp_url}/wp-json/wp/v2/pages"
    resp = requests.get(
        url,
        params={"slug": slug, "status": "publish,draft,private", "per_page": 1},
        headers=_wp_headers(wp_user, wp_pass, False),
        auth=(wp_user, wp_pass),
        timeout=30,
    )
    if resp.status_code != 200:
        return None
    pages = resp.json()
    if not pages:
        return None
    p = pages[0]
    return {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]}


def create_page(
    wp_url: str, wp_user: str, wp_pass: str,
    title: str, content: str, slug: str,
    parent_slug: str | None = None, status: str = "draft",
    template: str | None = None,
) -> dict:
    """Создаёт страницу. parent_slug → родитель; template → шаблон WP (page-landing.php и т.п.)."""
    parent_id = 0
    if parent_slug:
        parent = find_page(wp_url, wp_user, wp_pass, parent_slug)
        if parent:
            parent_id = parent["id"]

    url = f"{wp_url}/wp-json/wp/v2/pages"
    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": status,
        "parent": parent_id,
    }
    if template:
        payload["template"] = template
    resp = requests.post(
        url, json=payload,
        headers=_wp_headers(wp_user, wp_pass),
        auth=(wp_user, wp_pass),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Ошибка создания: {resp.status_code}\n{resp.text}")
    return resp.json()


def update_page(
    wp_url: str, wp_user: str, wp_pass: str,
    page_id: int, content: str, title: str | None = None, parent_id: int | None = None,
    template: str | None = None,
) -> dict:
    """Обновляет страницу. title, parent_id, template — при необходимости."""
    payload: dict = {"content": content}
    if title:
        payload["title"] = title
    if parent_id is not None:
        payload["parent"] = parent_id
    if template:
        payload["template"] = template
    url = f"{wp_url}/wp-json/wp/v2/pages/{page_id}"
    resp = requests.post(
        url, json=payload,
        headers=_wp_headers(wp_user, wp_pass),
        auth=(wp_user, wp_pass),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Ошибка обновления: {resp.status_code}\n{resp.text}")
    return resp.json()


# Порядок секций страницы залов (источник правды для рендера).
# pricing → equipment: тарифы раньше оснащения (UX).
# gallery → cases → testimonials: социальные доказательства перед FAQ.
SECTIONS_ORDER = [
    "hero",
    "for_whom",
    "benefits",
    "features",
    "pricing",
    "equipment",
    "booking_steps",
    "form",
    "gallery",
    "cases",
    "testimonials",
    "faq",
]


def _has_section_content(data: dict, section_key: str) -> bool:
    """Проверяет, есть ли в JSON контент для секции."""
    val = data.get(section_key)
    if val is None:
        return False
    if isinstance(val, dict):
        return bool(val)
    if isinstance(val, list):
        return len(val) > 0
    return True


def _render_section(section_key: str, data: dict) -> list[str]:
    """Рендерит одну секцию. Возвращает список HTML‑строк."""
    parts: list[str] = []

    if section_key == "hero":
        h = data.get("hero", {})
        if not h.get("title"):
            return []
        parts.append('<section class="landing-hero">')
        parts.append(f'  <h1>{_esc(h["title"])}</h1>')
        if h.get("subtitle"):
            parts.append(f'  <p class="landing-hero-subtitle">{_esc(h["subtitle"])}</p>')
        if h.get("price_line"):
            parts.append(f'  <p class="landing-hero-price">{_esc(h["price_line"])}</p>')
        if h.get("cta_primary"):
            parts.append(f'  <a href="#bron" class="button cta-primary">{_esc(h["cta_primary"])}</a>')
        parts.append("</section>")

    elif section_key == "for_whom":
        fw = data.get("for_whom", [])
        parts.append('<section class="landing-for-whom"><h2>Для кого</h2>')
        for item in fw:
            parts.append('  <div class="landing-card">')
            parts.append(f'    <h3>{_esc(item.get("title", ""))}</h3>')
            parts.append(f'    <p>{_esc(item.get("text", ""))}</p>')
            parts.append("  </div>")
        parts.append("</section>")

    elif section_key == "benefits":
        ben = data.get("benefits", [])
        parts.append('<section class="landing-benefits"><h2>Преимущества</h2>')
        for item in ben:
            parts.append('  <div class="landing-card">')
            parts.append(f'    <h3>{_esc(item.get("title", ""))}</h3>')
            parts.append(f'    <p>{_esc(item.get("text", ""))}</p>')
            parts.append("  </div>")
        parts.append("</section>")

    elif section_key == "features":
        feat = data.get("features", [])
        parts.append('<section class="landing-features"><h2>Характеристики</h2>')
        parts.append("  <dl>")
        for item in feat:
            parts.append(f'    <dt>{_esc(item.get("label", ""))}</dt>')
            parts.append(f'    <dd>{_esc(item.get("value", ""))}</dd>')
        parts.append("  </dl>")
        parts.append("</section>")

    elif section_key == "pricing":
        pr = data.get("pricing", [])
        parts.append('<section class="landing-pricing"><h2>Тарифы</h2>')
        for item in pr:
            parts.append('  <div class="landing-tariff">')
            parts.append(f'    <h4>{_esc(item.get("name", ""))}</h4>')
            parts.append(f'    <p>{_esc(item.get("description", ""))}</p>')
            parts.append(f'    <p class="price">{_esc(item.get("price", ""))}</p>')
            parts.append("  </div>")
        parts.append("</section>")

    elif section_key == "equipment":
        eq = data.get("equipment", [])
        parts.append('<section class="landing-equipment"><h2>Оснащение</h2>')
        for cat in eq:
            items = cat.get("items", [])
            if items:
                parts.append(f'  <h3>{_esc(cat.get("category", ""))}</h3>')
                parts.append("  <ul>")
                for it in items:
                    parts.append(f'    <li>{_esc(it)}</li>')
                parts.append("  </ul>")
        parts.append("</section>")

    elif section_key == "booking_steps":
        bs = data.get("booking_steps", [])
        parts.append('<section class="landing-booking-steps"><h2>Как забронировать</h2><ol>')
        for s in bs:
            parts.append(f'  <li>{_esc(s)}</li>')
        parts.append("</ol></section>")

    elif section_key == "form":
        form = data.get("form", {})
        fid = form.get("id", "bron")
        parts.append(f'<section class="landing-form" id="{_esc(fid)}">')
        parts.append(f'  <h2>{_esc(form.get("title", ""))}</h2>')
        parts.append(f'  <p>{_esc(form.get("description", ""))}</p>')
        parts.append("  <!-- форма вставляется шорткодом/виджетом -->")
        parts.append("</section>")

    elif section_key == "gallery":
        gallery = data.get("gallery", [])
        parts.append('<section class="landing-gallery"><h2>Как выглядит зал</h2>')
        for item in gallery:
            title = item.get("title", "")
            desc = item.get("description", "")
            img = item.get("image", "")
            parts.append('  <div class="landing-gallery-item">')
            if img:
                parts.append(f'    <img src="{_esc(img)}" alt="{_esc(title)}" />')
            parts.append(f'    <h4>{_esc(title)}</h4>')
            if desc:
                parts.append(f'    <p>{_esc(desc)}</p>')
            parts.append("  </div>")
        parts.append("</section>")

    elif section_key == "cases":
        cases = data.get("cases", [])
        parts.append('<section class="landing-cases"><h2>Кейсы мероприятий в нашем зале</h2>')
        for c in cases:
            parts.append('  <div class="landing-case">')
            parts.append(f'    <h3>{_esc(c.get("title", ""))}</h3>')
            if c.get("client"):
                parts.append(f'    <p class="landing-case-client">{_esc(c.get("client", ""))}</p>')
            if c.get("goal"):
                parts.append(f'    <p><strong>Задача:</strong> {_esc(c.get("goal", ""))}</p>')
            if c.get("result"):
                parts.append(f'    <p class="landing-case-result"><strong>Результат:</strong> {_esc(c.get("result", ""))}</p>')
            parts.append("  </div>")
        parts.append("</section>")

    elif section_key == "testimonials":
        testimonials = data.get("testimonials", [])
        parts.append('<section class="landing-testimonials"><h2>Отзывы организаторов</h2>')
        for t in testimonials:
            parts.append('  <blockquote class="landing-testimonial">')
            parts.append(f'    <p>{_esc(t.get("text", ""))}</p>')
            if t.get("author") or t.get("company"):
                auth = _esc(t.get("author", ""))
                comp = _esc(t.get("company", ""))
                parts.append(f'    <footer>— {auth}{", " + comp if comp else ""}</footer>')
            parts.append("  </blockquote>")
        parts.append("</section>")

    elif section_key == "faq":
        faq = data.get("faq", [])
        parts.append('<section class="landing-faq"><h2>Вопросы и ответы</h2>')
        for item in faq:
            parts.append('  <details>')
            parts.append(f'    <summary>{_esc(item.get("question", ""))}</summary>')
            parts.append(f'    <p>{_esc(item.get("answer", ""))}</p>')
            parts.append("  </details>")
        parts.append("</section>")

    return parts


def json_to_html(data: dict) -> str:
    """
    Конвертирует JSON‑блоки в семантический HTML.
    Порядок секций задаётся SECTIONS_ORDER (pricing перед equipment).
    Секции без контента не выводятся.
    """
    result: list[str] = []
    for section_key in SECTIONS_ORDER:
        if not _has_section_content(data, section_key):
            continue
        result.extend(_render_section(section_key, data))
    return "\n".join(result)


def _esc(s: str) -> str:
    """Простой escape для HTML."""
    if not isinstance(s, str):
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    # Windows: консоль cp1251 не поддерживает Unicode
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Публикация JSON‑лендингов конференц‑зала в WP")
    ap.add_argument("slug", nargs="?", help="Slug страницы (korporativnye-treningi, onlajn-shkoly, kouchting)")
    ap.add_argument("--dry-run", action="store_true", help="Только показать, без отправки")
    ap.add_argument("--output-html", action="store_true", help="Сохранить HTML в output/")
    args = ap.parse_args()

    pages_config = SHARED_CONFIG.get("konferenc_zal_pages", {})
    if not pages_config:
        print("[ERR] konferenc_zal_pages не найден в shared-config.json")
        sys.exit(1)

    page_template = pages_config.get("_page_template", "").strip() or None

    # Фильтр по slug
    if args.slug:
        if args.slug not in pages_config:
            print(f"[ERR] Slug '{args.slug}' не найден. Доступные: {', '.join(k for k in pages_config if not k.startswith('_'))}")
            sys.exit(1)
        pages_config = {args.slug: pages_config[args.slug]}

    for slug, cfg in pages_config.items():
        if slug.startswith("_"):
            continue
        json_name = cfg.get("json")
        if not json_name:
            continue

        json_path = DOCS_DIR / json_name
        if not json_path.exists():
            print(f"   [!] {slug}: JSON не найден {json_path}")
            continue

        data = json.loads(json_path.read_text("utf-8"))
        html = json_to_html(data)
        # menu_title — короткое имя для меню; иначе h1/hero.title
        menu_title = cfg.get("menu_title")
        page_title = menu_title or data.get("h1") or data.get("hero", {}).get("title", slug)

        print(f"[*] {slug}: {page_title}...")

        if args.output_html:
            out_path = OUTPUT_DIR / f"konferenc-zal-{slug}.html"
            out_path.write_text(html, encoding="utf-8")
            print(f"   → сохранено {out_path}")
            continue

        if args.dry_run:
            print(f"   [dry-run] HTML {len(html)} символов")
            continue

        try:
            wp_url, wp_user, wp_pass = _wp_auth()
            existing = find_page(wp_url, wp_user, wp_pass, slug)

            if existing:
                parent_slug = cfg.get("parent_slug")
                parent_id = None
                if parent_slug:
                    parent_page = find_page(wp_url, wp_user, wp_pass, parent_slug)
                    if parent_page:
                        parent_id = parent_page["id"]
                update_page(wp_url, wp_user, wp_pass, existing["id"], html, title=page_title, parent_id=parent_id, template=page_template)
                print(f"   [OK] Обновлено: {existing['link']}")
            else:
                parent = cfg.get("parent_slug", "konferenc-zal")
                new = create_page(wp_url, wp_user, wp_pass, page_title, html, slug, parent_slug=parent, template=page_template)
                print(f"   [OK] Создано: {new.get('link', '-')}")
        except Exception as e:
            print(f"   [ERR] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
