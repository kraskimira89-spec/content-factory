#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_sport_zal.py
Публикация/обновление лендинга «Спортивный зал» в WordPress
из файла output/sportivny-zal.json

Аналог: publish_konferenc_zal_from_md.py
Запуск: python publish_sport_zal.py
        python publish_sport_zal.py --draft
"""

import json
import os
import sys
import requests
from requests.auth import HTTPBasicAuth

# ─────────────────────────────────────────────
# 1. НАСТРОЙКИ — ЗАПОЛНИТЕ ОДИН РАЗ
# ─────────────────────────────────────────────

WP_URL   = "http://91.229.11.147"          # URL сайта (без слеша на конце)
WP_USER  = "admin"                          # Логин WordPress
WP_PASS  = "ВАШ_ПАРОЛЬ_ИЛИ_APP_PASSWORD"   # Пароль или Application Password WP

JSON_PATH = os.path.join(
    os.path.dirname(__file__),
    "output", "sportivny-zal.json"
)

# ─────────────────────────────────────────────
# 2. ЗАГРУЗКА JSON
# ─────────────────────────────────────────────

def load_data(path):
    if not os.path.exists(path):
        print(f"[ОШИБКА] Файл не найден: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# 3. ФОРМИРОВАНИЕ HTML-КОНТЕНТА СТРАНИЦЫ
# ─────────────────────────────────────────────

def build_html(d):
    parts = []

    # ── HERO ──────────────────────────────────
    hero = d.get("hero", {})
    parts.append(f"""
<section class="landing-hero">
  <div class="landing-hero__content">
    <h1 class="landing-hero__title">{hero.get('title','')}</h1>
    <p class="landing-hero__subtitle">{hero.get('subtitle','')}</p>
    <p class="landing-hero__price-line">{hero.get('price_line','')}</p>
    <a href="#landing-form" class="btn-primary">{hero.get('cta_primary','Записаться')}</a>
    <a href="#equipment" class="btn-outline">{hero.get('cta_secondary','Узнать о тренажёрах')}</a>
  </div>
</section>
""")

    # ── FOR WHOM ──────────────────────────────
    cards_html = ""
    for c in d.get("for_whom", []):
        cards_html += f"""
    <div class="landing__card">
      <h3 class="landing__card-title">{c['title']}</h3>
      <p class="landing__card-text">{c['text']}</p>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--white" id="for-whom">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Для кого подходит наш спортивный зал</h2>
    <div class="landing__cards-grid landing__cards-grid--3">{cards_html}
    </div>
  </div>
</section>
""")

    # ── BENEFITS ──────────────────────────────
    ben_html = ""
    for b in d.get("benefits", []):
        ben_html += f"""
    <div class="landing__card">
      <h3 class="landing__card-title">{b['title']}</h3>
      <p class="landing__card-text">{b['text']}</p>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--gray" id="benefits">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Почему выбирают спортивный зал «Энтузиаст»</h2>
    <div class="landing__cards-grid landing__cards-grid--2">{ben_html}
    </div>
  </div>
</section>
""")

    # ── EQUIPMENT ─────────────────────────────
    eq_html = ""
    for eq in d.get("equipment", []):
        feats = "".join(f"<li>{f}</li>" for f in eq.get("features", []))
        eq_html += f"""
    <div class="landing__equipment-card">
      <h3 class="landing__equipment-title">{eq['title']}</h3>
      <p class="landing__equipment-desc">{eq['description']}</p>
      <ul class="landing__equipment-features">{feats}</ul>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--white" id="equipment">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Оборудование спортивного зала</h2>
    <div class="landing__cards-grid landing__cards-grid--2">{eq_html}
    </div>
  </div>
</section>
""")

    # ── PROGRAMS ──────────────────────────────
    prog_html = ""
    for p in d.get("programs", []):
        price_main = f"{p['price_single']} ₽" if p.get("price_single") else p.get("price_note","по договорённости")
        price_sub  = f"10 занятий — {p['price_10']} ₽" if p.get("price_10") else ""
        prog_html += f"""
    <div class="landing__program-card">
      <h3 class="landing__program-title">{p['title']}</h3>
      <p class="landing__program-desc">{p['description']}</p>
      <p class="landing__program-duration">{p.get('duration_min',50)} мин</p>
      <p class="landing__program-price">{price_main}</p>
      {'<p class="landing__program-price-bulk">' + price_sub + '</p>' if price_sub else ''}
      <a href="#landing-form" class="btn-primary btn--full">{p.get('cta','Записаться')}</a>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--gray" id="programs">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Программы занятий в спортивном зале</h2>
    <div class="landing__cards-grid landing__cards-grid--3">{prog_html}
    </div>
  </div>
</section>
""")

    # ── PRICING ───────────────────────────────
    price_html = ""
    for t in d.get("pricing", []):
        highlight = ' landing__tariff-card--highlight' if t.get("highlight") else ''
        badge     = '<span class="landing__tariff-badge">Выгодно</span>' if t.get("highlight") else ''
        price_html += f"""
    <div class="landing__tariff-card{highlight}">
      {badge}
      <h3 class="landing__tariff-title">{t['title']}</h3>
      <p class="landing__tariff-desc">{t['description']}</p>
      <p class="landing__tariff-price">{t['price']}</p>
      <p class="landing__tariff-note">{t.get('price_note','')}</p>
      <a href="#landing-form" class="btn-primary btn--full">{t.get('cta','Записаться')}</a>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--white" id="pricing">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Тарифы на занятия в спортивном зале</h2>
    <div class="landing__cards-grid landing__cards-grid--4">{price_html}
    </div>
  </div>
</section>
""")

    # ── SYNERGY ───────────────────────────────
    syn_html = ""
    for s in d.get("synergy", []):
        syn_html += f"""
    <div class="landing__synergy-card">
      <h3 class="landing__synergy-title">{s['title']}</h3>
      <p class="landing__synergy-text">{s['text']}</p>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--accent" id="synergy">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Усиль результат — совмести зал с процедурами</h2>
    <p class="landing-section__subtitle">После тренировки тело лучше воспринимает восстановительные процедуры</p>
    <div class="landing__cards-grid landing__cards-grid--2">{syn_html}
    </div>
    <div class="landing-section__cta">
      <a href="#landing-form" class="btn-primary">Подобрать программу комплекса</a>
    </div>
  </div>
</section>
""")

    # ── BOOKING STEPS ─────────────────────────
    steps_html = ""
    for i, step in enumerate(d.get("booking_steps", []), 1):
        steps_html += f"""
    <div class="landing__step-card">
      <span class="landing__step-number">{i}</span>
      <p class="landing__step-text">{step}</p>
    </div>"""
    parts.append(f"""
<section class="landing-section landing-section--white" id="how-to-start">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Как начать заниматься в спортивном зале</h2>
    <div class="landing__steps">{steps_html}
    </div>
  </div>
</section>
""")

    # ── FORM ──────────────────────────────────
    form_d = d.get("form", {})
    fields_html = ""
    for fld in form_d.get("fields", []):
        if fld["type"] == "select":
            opts = "".join(f'<option value="{o}">{o}</option>' for o in fld.get("options", []))
            fields_html += f'<select name="{fld["name"]}" class="landing__form-field"><option value="">— {fld["label"]} —</option>{opts}</select>'
        else:
            fields_html += f'<input type="{fld["type"]}" name="{fld["name"]}" placeholder="{fld["label"]}" class="landing__form-field" required>'
    parts.append(f"""
<section class="landing-section landing-section--gray" id="landing-form">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">{form_d.get('title','Записаться на тренировку')}</h2>
    <p class="landing-section__subtitle">{form_d.get('description','')}</p>
    <div class="landing__form-wrap">
      <form class="landing__form" method="post" action="/wp-json/contact-form-7/v1/contact-forms/FORM_ID/feedback">
        {fields_html}
        <button type="submit" class="btn-primary btn--full">{form_d.get('submit_text','Записаться')}</button>
        <p class="landing__form-cta-note">Ответим в течение 15–30 минут.</p>
      </form>
    </div>
  </div>
</section>
""")

    # ── GALLERY placeholder ────────────────────
    gal = d.get("gallery", {})
    parts.append(f"""
<section class="landing-section landing-section--white" id="gallery">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">{gal.get('title','Наш спортивный зал')}</h2>
    <p class="landing-section__subtitle">{gal.get('description','')}</p>
    <!-- Галерея: добавьте shortcode [gallery ids="..."] или блок WP -->
    [gallery columns="3" link="file"]
  </div>
</section>
""")

    # ── TESTIMONIALS ──────────────────────────
    t_html = ""
    for t in d.get("testimonials", []):
        t_html += f"""
    <div class="landing__testimonial-card">
      <p class="landing__testimonial-text">«{t['text']}»</p>
      <p class="landing__testimonial-author">— {t['author']}</p>
    </div>"""
    if t_html:
        parts.append(f"""
<section class="landing-section landing-section--gray" id="testimonials">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Отзывы клиентов спортивного зала</h2>
    <div class="landing__cards-grid landing__cards-grid--3">{t_html}
    </div>
  </div>
</section>
""")

    # ── FAQ ───────────────────────────────────
    faq_html = ""
    for q in d.get("faq", []):
        faq_html += f"""
    <details class="landing__faq-item">
      <summary class="landing__faq-question">{q['question']}</summary>
      <div class="landing__faq-answer"><p>{q['answer']}</p></div>
    </details>"""
    parts.append(f"""
<section class="landing-section landing-section--white" id="faq">
  <div class="landing-section__inner">
    <h2 class="landing-section__title">Частые вопросы о спортивном зале</h2>
    <div class="landing__faq">{faq_html}
    </div>
  </div>
</section>
""")

    return "\n".join(parts)


# ─────────────────────────────────────────────
# 4. ПОИСК СТРАНИЦЫ В WORDPRESS ПО SLUG
# ─────────────────────────────────────────────

def find_page_by_slug(slug, auth):
    url = f"{WP_URL}/wp-json/wp/v2/pages"
    resp = requests.get(url, params={"slug": slug, "per_page": 1}, auth=auth, timeout=15)
    resp.raise_for_status()
    pages = resp.json()
    return pages[0] if pages else None


# ─────────────────────────────────────────────
# 5. СОЗДАНИЕ ИЛИ ОБНОВЛЕНИЕ СТРАНИЦЫ
# ─────────────────────────────────────────────

def publish_page(d, content_html, draft=False, auth=None):
    slug   = d["meta"]["slug"]              # sport-zal
    status = "draft" if draft else "publish"

    payload = {
        "slug":             slug,
        "title":            d.get("meta_title", "Спортивный зал"),
        "content":          content_html,
        "status":           status,
        "meta": {
            "_yoast_wpseo_title":    d.get("meta_title", ""),
            "_yoast_wpseo_metadesc": d.get("meta_description", ""),
        }
    }

    existing = find_page_by_slug(slug, auth)

    if existing:
        page_id = existing["id"]
        url = f"{WP_URL}/wp-json/wp/v2/pages/{page_id}"
        resp = requests.post(url, json=payload, auth=auth, timeout=30)
        resp.raise_for_status()
        print(f"[OK] Страница обновлена: {WP_URL}/{slug}/ (ID {page_id})")
    else:
        url = f"{WP_URL}/wp-json/wp/v2/pages"
        # Установить родительскую страницу /services/ (найти её ID)
        parent = find_page_by_slug("services", auth)
        if parent:
            payload["parent"] = parent["id"]
        resp = requests.post(url, json=payload, auth=auth, timeout=30)
        resp.raise_for_status()
        new_id = resp.json().get("id")
        print(f"[OK] Страница создана: {WP_URL}/services/{slug}/ (ID {new_id})")

    return resp.json()


# ─────────────────────────────────────────────
# 6. ТОЧКА ВХОДА
# ─────────────────────────────────────────────

def main():
    draft = "--draft" in sys.argv

    print(f"[1/4] Загрузка данных из: {JSON_PATH}")
    data = load_data(JSON_PATH)

    print("[2/4] Формирование HTML...")
    html = build_html(data)

    print(f"[3/4] Подключение к WordPress: {WP_URL}")
    auth = HTTPBasicAuth(WP_USER, WP_PASS)

    print(f"[4/4] Публикация страницы (draft={draft})...")
    result = publish_page(data, html, draft=draft, auth=auth)

    link = result.get("link", "—")
    print(f"\n✅ Готово! Ссылка: {link}")
    if draft:
        print("   Статус: ЧЕРНОВИК (передайте --draft убрать для публикации)")


if __name__ == "__main__":
    main()
