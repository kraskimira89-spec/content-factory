"""
Публикация страницы конференц-зала из Markdown (вывод агентов 1-4).

Читает последний файл *_page_Конференц-зал_Ноябрьск.md из output/,
конвертирует в HTML по схеме docs/landing-zaly-wireframe.md (чередование блоков),
публикует в WordPress под /services/konferenc-zal/ с шаблоном «Лендинг Конференц-зал».

Использование:
  python scripts/publish_konferenc_zal_from_md.py
  python scripts/publish_konferenc_zal_from_md.py --dry-run
  python scripts/publish_konferenc_zal_from_md.py --input output/20250101_123456_page_Конференц-зал_Ноябрьск.md
"""
from __future__ import annotations

import argparse
import base64
import os
import re
from pathlib import Path

import markdown
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIG_DIR = PROJECT_ROOT / "config"

load_dotenv(CONFIG_DIR / ".env")


def _esc(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def find_last_page_md() -> Path | None:
    """Ищет последний *_page_Конференц-зал_Ноябрьск.md в output."""
    pattern = "*_page_Конференц-зал_Ноябрьск.md"
    files = list(OUTPUT_DIR.glob(pattern))
    if not files:
        pattern2 = "*_page_Конференц*_Ноябрьск.md"
        files = list(OUTPUT_DIR.glob(pattern2))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def parse_md_sections(md_text: str) -> list[tuple[str, str]]:
    """Разбивает MD по ## заголовкам. Возвращает [(title, content), ...]."""
    sections = []
    parts = re.split(r"\n##\s+", md_text, flags=re.IGNORECASE)
    # Первая часть — до первого H2 (H1, лид)
    lead = parts[0].strip()
    if lead:
        m = re.match(r"#\s+(.+?)(?:\n|$)", lead)
        h1 = m.group(1).strip() if m else "Конференц‑зал в Ноябрьске"
        rest = re.sub(r"^#\s+.+?\n", "", lead, count=1)
        sections.append(("Hero", f"{h1}\n\n{rest}"))

    for block in parts[1:]:
        lines = block.strip().split("\n", 1)
        title = lines[0].strip().rstrip("#").strip()
        content = lines[1] if len(lines) > 1 else ""
        content = content.strip()
        # Убираем image_slot комментарии из контента для HTML
        content = re.sub(r"<!--\s*image_slot:\s*\w+\s*-->\s*", "", content)
        if title or content:
            sections.append((title, content))

    return sections


def md_to_html(text: str) -> str:
    """Конвертирует MD-фрагмент в HTML."""
    html = markdown.markdown(text, extensions=["extra", "tables", "sane_lists"])
    return html.strip()


def _section_key(title: str) -> str | None:
    """Определяет тип секции по заголовку."""
    t = title.lower()
    if "hero" in t:
        return "hero"
    if "для каких мероприятий" in t or "для кого" in t:
        return "for_whom"
    if "почему организаторам" in t or "преимущества" in t:
        return "benefits"
    if "как выглядит" in t or "галерея" in t:
        return "gallery"
    if "характеристики" in t:
        return "features"
    if "оснащение" in t:
        return "equipment"
    if "тарифы" in t:
        return "pricing"
    if "как забронировать" in t:
        return "booking"
    if "оставить заявку" in t or "заявку" in t:
        return "form"
    if "кейсы" in t:
        return "cases"
    if "отзывы" in t:
        return "testimonials"
    if "частые вопросы" in t or "вопросы" in t:
        return "faq"
    return None


def _extract_price_from_hero(hero_content: str) -> int:
    """Извлекает цену «от X ₽» из hero-контента. По умолчанию 1500."""
    m = re.search(r"от\s+(\d+)\s*₽|от\s+(\d+)\s+руб", hero_content, re.IGNORECASE)
    if m:
        return int(m.group(1) or m.group(2) or 1500)
    return 1500


def sections_to_landing_html(sections: list[tuple[str, str]], wp_url: str = "") -> str:
    """Преобразует секции в HTML по схеме чередования блоков.
    wp_url: базовый URL сайта для CTA (форма заявки на главной).
    """
    out = []
    blocks = {
        "hero": "", "for_whom": "", "benefits": "", "gallery": "",
        "features": "", "equipment": "", "pricing": "", "booking": "",
        "form": "", "cases": "", "testimonials": "", "faq": "",
    }
    for title, content in sections:
        key = _section_key(title)
        if key and key in blocks:
            blocks[key] = content
        elif key == "hero":
            blocks["hero"] = content
    hero_content = blocks["hero"]
    for_whom = blocks["for_whom"]
    benefits = blocks["benefits"]
    gallery = blocks["gallery"]
    features = blocks["features"]
    equipment = blocks["equipment"]
    pricing = blocks["pricing"]
    booking = blocks["booking"]
    form_block = blocks["form"]
    cases = blocks["cases"]
    testimonials = blocks["testimonials"]
    faq = blocks["faq"]

    # Hero: парсим H1, лид, цену; CTA ведёт на форму главной
    price = _extract_price_from_hero(hero_content)
    contact_url = f"{wp_url.rstrip('/')}/?from=konferenc-zal#contact-form" if wp_url else "#bron"
    lines = hero_content.split("\n")
    h1 = ""
    for line in lines:
        if line.startswith("# "):
            h1 = line.lstrip("# ").strip()
            break
    lead = "\n".join([l for l in lines if not l.startswith("#") and l.strip()])
    lead_html = md_to_html(lead) if lead else ""
    cta_match = re.search(r"\[([^\]]+)\]\(#bron\)", hero_content)
    cta_text = cta_match.group(1) if cta_match else "Забронировать зал"

    out.append('<section class="landing-hero">')
    if h1:
        out.append(f"  <h1>{_esc(h1)}</h1>")
    if lead_html:
        out.append(f"  <div class=\"landing-hero-subtitle\">{lead_html}</div>")
    out.append(f'  <p class="landing-hero-price">Почасовая аренда от {price} ₽ · до 40 человек · центр «Энтузиаст»</p>')
    out.append(f'  <a href="{_esc(contact_url)}" class="button cta-primary">{_esc(cta_text)}</a>')
    out.append("</section>")

    # Два в ряд: Для кого | Преимущества (H2 по wireframe)
    if for_whom or benefits:
        out.append('<section class="landing-row-two-cols">')
        if for_whom:
            out.append('  <div class="landing-col landing-for-whom">')
            out.append("    <h2>Для каких мероприятий подходит зал</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(for_whom)}</div>")
            out.append("  </div>")
        if benefits:
            out.append('  <div class="landing-col landing-benefits">')
            out.append("    <h2>Почему организаторам удобно проводить мероприятия у нас</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(benefits)}</div>")
            out.append("  </div>")
        out.append("</section>")

    # Галерея (картинка во всю ширину)
    if gallery:
        out.append('<section class="landing-gallery"><h2>Как выглядит зал</h2>')
        out.append(f"  <div class=\"landing-gallery-content\">{md_to_html(gallery)}</div>")
        out.append("</section>")

    # 1. Характеристики + Оснащение — один ряд, два блока рядом
    if features or equipment:
        out.append('<section class="landing-row-two-cols landing-features-equipment">')
        if features:
            out.append('  <div class="landing-col landing-features">')
            out.append("    <h2>Характеристики зала</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(features)}</div>")
            out.append("  </div>")
        if equipment:
            out.append('  <div class="landing-col landing-equipment">')
            out.append("    <h2>Оснащение конференц‑зала</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(equipment)}</div>")
            out.append("  </div>")
        out.append("</section>")

    # Фото во всю ширину (слот для изображения)
    out.append('<section class="landing-photo-full"><div class="landing-photo-placeholder"><p>Фото зала</p></div></section>')

    # 2. Тарифы + Как забронировать — один ряд, два блока
    if pricing or booking:
        out.append('<section class="landing-row-two-cols landing-pricing-booking">')
        if pricing:
            out.append('  <div class="landing-col landing-pricing">')
            out.append("    <h2>Тарифы</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(pricing)}</div>")
            out.append("  </div>")
        if booking:
            out.append('  <div class="landing-col landing-booking">')
            out.append("    <h2>Как забронировать</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(booking)}</div>")
            out.append("  </div>")
        out.append("</section>")

    # Фото во всю ширину (слот для изображения)
    out.append('<section class="landing-photo-full"><div class="landing-photo-placeholder"><p>Фото зала</p></div></section>')

    # 3. Форма + Кейсы — один ряд (форма слева, кейсы справа)
    if form_block or cases:
        out.append('<section class="landing-row-two-cols landing-form-cases" id="bron">')
        if form_block:
            form_html = md_to_html(form_block)
            if contact_url:
                form_html = form_html.replace('href="#bron"', f'href="{_esc(contact_url)}"')
            out.append('  <div class="landing-col landing-form">')
            out.append("    <h2>Оставить заявку</h2>")
            out.append(f"    <div class=\"landing-col-content\">{form_html}</div>")
            out.append("  </div>")
        if cases:
            out.append('  <div class="landing-col landing-cases">')
            out.append("    <h2>Кейсы</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(cases)}</div>")
            out.append("  </div>")
        out.append("</section>")

    # Фото во всю ширину (слот для изображения)
    out.append('<section class="landing-photo-full"><div class="landing-photo-placeholder"><p>Фото зала</p></div></section>')

    # 4. Отзывы + FAQ — один ряд, два блока
    if testimonials or faq:
        out.append('<section class="landing-row-two-cols landing-testimonials-faq">')
        if testimonials:
            out.append('  <div class="landing-col landing-testimonials">')
            out.append("    <h2>Отзывы организаторов</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(testimonials)}</div>")
            out.append("  </div>")
        if faq:
            out.append('  <div class="landing-col landing-faq">')
            out.append("    <h2>Частые вопросы</h2>")
            out.append(f"    <div class=\"landing-col-content\">{md_to_html(faq)}</div>")
            out.append("  </div>")
        out.append("</section>")

    return "\n".join(out)


def wp_publish(html: str, title: str, dry_run: bool) -> str | None:
    """Публикует страницу в WP. Возвращает link или None."""
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_pass]):
        raise RuntimeError("Задайте WP_URL, WP_USERNAME, WP_APP_PASSWORD в config/.env")

    token = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    # Ищем страницу konferenc-zal
    r = requests.get(
        f"{wp_url}/wp-json/wp/v2/pages",
        params={"slug": "konferenc-zal", "status": "publish,draft,private", "per_page": 1},
        headers={"Authorization": f"Basic {token}"},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"WP API: {r.status_code}")

    pages = r.json()
    parent_id = 0
    parent = requests.get(
        f"{wp_url}/wp-json/wp/v2/pages",
        params={"slug": "services", "per_page": 1},
        headers={"Authorization": f"Basic {token}"},
        timeout=30,
    )
    if parent.status_code == 200 and parent.json():
        parent_id = parent.json()[0]["id"]

    if dry_run:
        print(f"[dry-run] HTML {len(html)} символов")
        return None

    template = "template-page-landing-konferenc-zal.php"
    if pages:
        page_id = pages[0]["id"]
        resp = requests.post(
            f"{wp_url}/wp-json/wp/v2/pages/{page_id}",
            json={"content": html, "template": template},
            headers=headers,
            timeout=30,
        )
    else:
        resp = requests.post(
            f"{wp_url}/wp-json/wp/v2/pages",
            json={
                "title": title,
                "content": html,
                "slug": "konferenc-zal",
                "parent": parent_id,
                "status": "draft",
                "template": template,
            },
            headers=headers,
            timeout=30,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"WP API: {resp.status_code}\n{resp.text}")
    return resp.json().get("link", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", help="Путь к MD-файлу")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    md_path = Path(args.input) if args.input else find_last_page_md()
    if not md_path or not md_path.is_file():
        print("[ERR] Не найден *_page_Конференц-зал_Ноябрьск.md в output/")
        print("      Сначала выполните: python scripts/run_konferenc_zal_chain.py --stop-after 4")
        return 1

    print(f"[*] Читаю {md_path.name}")
    md_text = md_path.read_text(encoding="utf-8")
    # Убираем обёртку ```markdown ... ``` если есть
    if md_text.strip().startswith("```"):
        md_text = re.sub(r"^```\w*\n", "", md_text)
        md_text = re.sub(r"\n```\s*$", "", md_text)

    sections = parse_md_sections(md_text)
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    html = sections_to_landing_html(sections, wp_url=wp_url)

    title = "Конференц‑зал 72 м² в Ноябрьске"
    link = wp_publish(html, title, args.dry_run)
    if link:
        print(f"[OK] Опубликовано: {link}")
    return 0


if __name__ == "__main__":
    exit(main() or 0)
