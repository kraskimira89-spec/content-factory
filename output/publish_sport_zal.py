#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_sport_zal.py (копия в output/)
Публикация/обновление лендинга «Спортивный зал» в WordPress
из файла output/sportivny-zal.json. Синхронизировано с корневым publish_sport_zal.py:
классы landing__*, .env, template в API, _esc, wp_url. Секции: Programs, Indications,
порядок по ТЗ (Form → Gallery → Testimonials → FAQ).

Запуск из корня проекта: python output/publish_sport_zal.py [--draft]
"""

import json
import os
import sys
import requests
from requests.auth import HTTPBasicAuth

# .env из корня проекта (config/.env)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_script_dir)
CONFIG_DIR = os.path.join(_root_dir, "config")
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
if load_dotenv:
    load_dotenv(os.path.join(CONFIG_DIR, ".env"))

def _get_wp_credentials():
    wp_url = (os.getenv("WP_URL") or "").strip().rstrip("/")
    wp_user = (os.getenv("WP_USERNAME") or "").strip()
    wp_pass = (os.getenv("WP_APP_PASSWORD") or "").strip()
    if not wp_url or not wp_user or not wp_pass:
        raise RuntimeError(
            "Задайте WP_URL, WP_USERNAME, WP_APP_PASSWORD в config/.env"
        )
    try:
        (wp_user + ":" + wp_pass).encode("latin1")
    except UnicodeEncodeError:
        raise RuntimeError(
            "WP_USERNAME и WP_APP_PASSWORD должны содержать только символы Latin-1 (ASCII). "
            "Используйте Application Password из WordPress (профиль → Безопасность приложений)."
        )
    return wp_url, wp_user, wp_pass

JSON_PATH = os.path.join(_script_dir, "sportivny-zal.json")


def load_data(path):
    if not os.path.exists(path):
        print(f"[ОШИБКА] Файл не найден: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_html(d):
    parts = []

    # ── 1. HERO ──────────── (разметка landing-hero + landing-hero__ctas для одной строки кнопок)
    hero = d.get("hero", {})
    parts.append(f"""
<section class="landing-hero" id="landing-hero">
  <div class="landing-hero__content">
    <h1 class="landing-hero__title">{_esc(hero.get('title',''))}</h1>
    <p class="landing-hero__subtitle">{_esc(hero.get('subtitle',''))}</p>
    <p class="landing-hero__price-line">{_esc(hero.get('price_line',''))}</p>
    <div class="landing-hero__ctas">
      <a class="btn-primary" href="#landing-form">{_esc(hero.get('cta_primary','Записаться на тренировку'))}</a>
      <a class="btn-outline" href="#equipment">{_esc(hero.get('cta_secondary','Узнать о тренажёрах'))}</a>
    </div>
  </div>
</section>
""")

    # ── 2. ДЛЯ КОГО ──
    for_whom = d.get("for_whom", [])
    n_cards = len(for_whom)
    cards_class = "landing__audience-cards--six" if n_cards >= 6 else "landing__audience-cards--4"
    cards_html = "".join(
        f'<div class="landing__audience-card"><h3 class="landing__audience-card-title">{_esc(c["title"])}</h3><p>{_esc(c["text"])}</p></div>'
        for c in for_whom
    )
    parts.append(f"""
<section class="landing__audience-equipment landing__section" id="for-whom">
  <div class="landing__container">
    <h2 class="landing__section-title">Для кого подходит наш спортивный зал</h2>
    <p class="landing__section-subtitle">Универсальное пространство для здоровья и формы.</p>
    <div class="landing__audience-cards {cards_class}">{cards_html}
    </div>
  </div>
</section>
""")

    # ── 3. ПРЕИМУЩЕСТВА ──
    ben_html = "".join(
        f'<div class="landing__advantage-card"><span class="landing__advantage-icon" aria-hidden="true">✓</span><span class="landing__advantage-text">{_esc(b["title"])}</span></div>'
        for b in d.get("benefits", [])
    )
    if ben_html:
        parts.append(f"""
<section class="landing__section landing__advantages-block" id="benefits">
  <div class="landing__container">
    <h2 class="landing__section-title">Почему выбирают спортивный зал «Энтузиаст»</h2>
    <p class="landing__section-subtitle">Безопасные нагрузки и синергия с процедурами центра.</p>
    <div class="landing__advantages-cards">{ben_html}
    </div>
  </div>
</section>
""")

    # ── 3b. ПОКАЗАНИЯ ──
    indications = d.get("indications", [])
    if indications:
        ind_items = "".join(f"<li>{_esc(item)}</li>" for item in indications)
        parts.append(f"""
<section class="landing__section landing__advantages-block" id="indications">
  <div class="landing__container">
    <h2 class="landing__section-title">Показания к применению</h2>
    <p class="landing__section-subtitle">Зал показан при следующих состояниях (рекомендуется консультация специалиста).</p>
    <ul class="landing__advantages-list landing__indications-list">{ind_items}
    </ul>
  </div>
</section>
""")

    # ── 4. ОБОРУДОВАНИЕ ──
    eq_list = d.get("equipment", [])
    eq_html = ""
    for i, eq in enumerate(eq_list):
        mod = "landing__equipment-card--coral" if i % 2 == 0 else "landing__equipment-card--teal"
        feats = "".join(f"<li>{_esc(f)}</li>" for f in eq.get("features", []))
        eq_html += f"""
    <div class="landing__equipment-card {mod}">
      <h3 class="landing__equipment-card-title">{_esc(eq.get('title',''))}</h3>
      <p class="landing__equipment-card-desc">{_esc(eq.get('description',''))}</p>
      <ul class="landing__equipment-card-list">{feats}</ul>
    </div>"""
    if eq_html:
        parts.append(f"""
<section class="landing__equipment-cards-block landing__section" id="equipment">
  <div class="landing__container">
    <p class="landing__equipment-badge">Оборудование</p>
    <h2 class="landing__section-title">Оборудование спортивного зала</h2>
    <p class="landing__section-subtitle">Пневматика HUR и силовые IRON KING — для здоровья и результата.</p>
    <div class="landing__equipment-cards-grid">{eq_html}
    </div>
  </div>
</section>
""")

    # ── 5. ПРОГРАММЫ ЗАНЯТИЙ ──
    programs = d.get("programs", [])
    prog_html = ""
    for p in programs:
        price_main = f"{p['price_single']} ₽" if p.get("price_single") else _esc(p.get("price_note", "по договорённости"))
        price_sub = f"10 занятий — {p['price_10']} ₽" if p.get("price_10") else ""
        prog_html += f"""
    <div class="landing__tariff">
      <h3 class="landing__tariff-name">{_esc(p.get('title',''))}</h3>
      <p class="landing__tariff-desc">{_esc(p.get('description',''))}</p>
      <p class="landing__tariff-note">{p.get('duration_min', 50)} мин · {price_main}</p>
      {('<p class="landing__tariff-note">' + _esc(price_sub) + '</p>') if price_sub else ''}
      <a href="#landing-contact" class="btn btn--coral">{_esc(p.get('cta','Записаться'))}</a>
    </div>"""
    if prog_html:
        parts.append(f"""
<section class="landing__tariffs landing__section" id="programs">
  <div class="landing__container">
    <h2 class="landing__section-title">Программы занятий в спортивном зале</h2>
    <p class="landing__section-subtitle">50 минут на выбор. Групповые и индивидуальные занятия.</p>
    <div class="landing__tariffs-grid landing__programs-grid">{prog_html}
    </div>
  </div>
</section>
""")

    # ── 6. ТАРИФЫ ──
    price_html = ""
    for t in d.get("pricing", []):
        popular = " landing__tariff--popular" if t.get("highlight") else ""
        badge = '<span class="landing__tariff-badge">Выгодно</span>' if t.get("highlight") else ''
        price_html += f"""
    <div class="landing__tariff{popular}">
      {badge}
      <h3 class="landing__tariff-name">{_esc(t['title'])}</h3>
      <p class="landing__tariff-price">{_esc(t['price'])}</p>
      <p class="landing__tariff-desc">{_esc(t.get('description',''))}</p>
      <p class="landing__tariff-note">{_esc(t.get('price_note',''))}</p>
      <a href="#landing-contact" class="btn btn--coral">{_esc(t.get('cta','Записаться'))}</a>
    </div>"""
    parts.append(f"""
<section class="landing__tariffs landing__section" id="landing-tariffs">
  <div class="landing__container">
    <h2 class="landing__section-title">Тарифы на занятия</h2>
    <p class="landing__section-subtitle">Выберите формат под свои цели.</p>
    <div class="landing__tariffs-grid">{price_html}
    </div>
  </div>
</section>
""")

    # ── 7. СИНЕРГИЯ ──
    syn_list = d.get("synergy", [])
    syn_html = "".join(
        f'<div class="landing__feature-card"><span class="landing__feature-icon landing__feature-icon--{"coral" if i % 2 == 0 else "teal"}" aria-hidden="true">+</span><h3 class="landing__feature-card-title">{_esc(s["title"])}</h3><p class="landing__feature-card-desc">{_esc(s["text"])}</p></div>'
        for i, s in enumerate(syn_list)
    )
    if syn_html:
        parts.append(f"""
<section class="landing__features-cards landing__section" id="synergy">
  <div class="landing__container">
    <h2 class="landing__section-title">Усиль результат — совмести зал с процедурами</h2>
    <p class="landing__section-subtitle">После тренировки тело лучше воспринимает восстановительные процедуры.</p>
    <div class="landing__features-grid">{syn_html}
    </div>
    <a href="#landing-contact" class="btn btn--coral">Подобрать программу комплекса</a>
  </div>
</section>
""")

    # ── 8. КАК НАЧАТЬ ──
    steps_html = "".join(
        f'<div class="landing__booking-step-card"><span class="landing__booking-step-num" aria-hidden="true">{i}</span><h3 class="landing__booking-step-title">Шаг {i}</h3><p>{_esc(step)}</p></div>'
        for i, step in enumerate(d.get("booking_steps", []), 1)
    )
    if steps_html:
        parts.append(f"""
<section class="landing__booking landing__section" id="how-to-start">
  <div class="landing__container landing__booking-full">
    <h2 class="landing__section-title">Как начать заниматься</h2>
    <div class="landing__booking-cards">{steps_html}
    </div>
    <p class="landing__booking-cta"><a href="#landing-contact" class="btn btn--primary btn--large">Записаться на тренировку</a></p>
  </div>
</section>
""")

    # ── 9. ФОРМА ──
    form_d = d.get("form", {})
    fields_html = ""
    for fld in form_d.get("fields", []):
        if fld.get("type") == "select":
            opts = "".join(f'<option value="{_esc(o)}">{_esc(o)}</option>' for o in fld.get("options", []))
            fields_html += f'<p class="landing__form-row"><label for="landing-{fld["name"]}">{_esc(fld["label"])}</label><select name="{_esc(fld["name"])}" id="landing-{fld["name"]}" class="landing__form-input"><option value="">— Выберите —</option>{opts}</select></p>'
        else:
            fields_html += f'<p class="landing__form-row"><label for="landing-{fld["name"]}">{_esc(fld["label"])}</label><input type="{_esc(fld.get("type","text"))}" name="{_esc(fld["name"])}" id="landing-{fld["name"]}" class="landing__form-input" placeholder="{_esc(fld.get("label",""))}" required></p>'
    parts.append(f"""
<section class="landing__form-block landing__section" id="landing-contact">
  <div class="landing__container">
    <h2 class="landing__section-title">{_esc(form_d.get('title','Записаться на тренировку'))}</h2>
    <p class="landing__section-subtitle">{_esc(form_d.get('description',''))}</p>
    <form class="landing__form landing__form--booking" action="#landing-contact" method="get">
      {fields_html}
      <p class="landing__form-row"><button type="submit" class="btn btn--coral btn--large">{_esc(form_d.get('submit_text','Записаться'))}</button></p>
      <p class="landing__form-note">Ответим в течение 15–30 минут.</p>
    </form>
  </div>
</section>
""")

    # ── 10. ГАЛЕРЕЯ (после формы по ТЗ) ──
    gal = d.get("gallery", {})
    parts.append(f"""
<section class="landing__gallery landing__section" id="gallery">
  <div class="landing__container">
    <h2 class="landing__section-title">{_esc(gal.get('title','Наш спортивный зал'))}</h2>
    <p class="landing__section-subtitle">{_esc(gal.get('description',''))}</p>
    <div class="landing__gallery-grid landing__gallery-grid--2x2">
      <div class="landing__gallery-grid-item landing__gallery-placeholder"><span class="landing__img-placeholder">Фото зала</span></div>
      <div class="landing__gallery-grid-item landing__gallery-placeholder"><span class="landing__img-placeholder">Фото зала</span></div>
    </div>
  </div>
</section>
""")

    # ── 11. ОТЗЫВЫ ──
    testimonials = d.get("testimonials", [])
    t_html = ""
    for i, t in enumerate(testimonials):
        initial = (t.get("author") or "?")[0].upper()
        mod = "landing__review-avatar--coral" if i % 2 == 0 else "landing__review-avatar--teal"
        t_html += f"""
    <blockquote class="landing__review-card">
      <div class="landing__review-stars" aria-hidden="true">★★★★★</div>
      <span class="landing__review-quote" aria-hidden="true">"</span>
      <p class="landing__review-text">«{_esc(t['text'])}»</p>
      <footer class="landing__review-footer">
        <span class="landing__review-avatar {mod}" aria-hidden="true">{_esc(initial)}</span>
        <cite class="landing__review-name">— {_esc(t.get('author',''))}</cite>
      </footer>
    </blockquote>"""
    if t_html:
        parts.append(f"""
<section class="landing__reviews-organizers landing__section" id="testimonials">
  <div class="landing__container">
    <span class="landing__reviews-badge">Отзывы</span>
    <h2 class="landing__section-title">Отзывы о спортивном зале</h2>
    <p class="landing__section-subtitle">Наши клиенты рекомендуют занятия в центре.</p>
    <div class="landing__reviews-grid">{t_html}
    </div>
  </div>
</section>
""")

    # ── 12. FAQ ──
    faq_items = d.get("faq", [])
    faq_html = ""
    for i, q in enumerate(faq_items):
        qid = f"faq-gym-{i+1}"
        aid = f"faq-gym-a{i+1}"
        faq_html += f"""
    <div class="landing__faq-item">
      <button type="button" class="landing__faq-dt" aria-expanded="false" aria-controls="{aid}" id="{qid}">{_esc(q['question'])}</button>
      <div id="{aid}" class="landing__faq-dd" aria-labelledby="{qid}" role="region" hidden><p>{_esc(q['answer'])}</p></div>
    </div>"""
    if faq_html:
        parts.append(f"""
<section class="landing__faq-cta landing__section" id="faq">
  <div class="landing__container">
    <h2 class="landing__section-title">Частые вопросы о спортивном зале</h2>
    <p class="landing__section-subtitle">Ответы на популярные вопросы.</p>
    <div class="landing__faq-list landing__faq-accordion" role="list">{faq_html}
    </div>
  </div>
</section>
""")

    return "\n".join(parts)


def find_page_by_slug(slug, auth, wp_url):
    url = f"{wp_url}/wp-json/wp/v2/pages"
    resp = requests.get(url, params={"slug": slug, "per_page": 1}, auth=auth, timeout=15)
    resp.raise_for_status()
    pages = resp.json()
    return pages[0] if pages else None


def publish_page(d, content_html, wp_url, draft=False, auth=None):
    slug = d["meta"]["slug"]
    status = "draft" if draft else "publish"
    template = d.get("meta", {}).get("page_template", "template-page-landing-trenazhernyy-zal.php")
    payload = {
        "slug": slug,
        "title": d.get("meta_title", "Спортивный зал"),
        "content": content_html,
        "status": status,
        "template": template,
        "meta": {
            "_yoast_wpseo_title": d.get("meta_title", ""),
            "_yoast_wpseo_metadesc": d.get("meta_description", ""),
        }
    }
    existing = find_page_by_slug(slug, auth, wp_url)
    if existing:
        page_id = existing["id"]
        url = f"{wp_url}/wp-json/wp/v2/pages/{page_id}"
        resp = requests.post(url, json=payload, auth=auth, timeout=30)
        resp.raise_for_status()
        print(f"[OK] Страница обновлена: {wp_url}/{slug}/ (ID {page_id})")
    else:
        url = f"{wp_url}/wp-json/wp/v2/pages"
        parent = find_page_by_slug("services", auth, wp_url)
        if parent:
            payload["parent"] = parent["id"]
        resp = requests.post(url, json=payload, auth=auth, timeout=30)
        resp.raise_for_status()
        new_id = resp.json().get("id")
        print(f"[OK] Страница создана: {wp_url}/services/{slug}/ (ID {new_id})")
    return resp.json()


def main():
    draft = "--draft" in sys.argv
    wp_url, wp_user, wp_pass = _get_wp_credentials()
    print(f"[1/4] Загрузка данных из: {JSON_PATH}")
    data = load_data(JSON_PATH)
    print("[2/4] Формирование HTML...")
    html = build_html(data)
    print(f"[3/4] Подключение к WordPress: {wp_url}")
    auth = HTTPBasicAuth(wp_user, wp_pass)
    print(f"[4/4] Публикация страницы (draft={draft})...")
    try:
        result = publish_page(data, html, wp_url, draft=draft, auth=auth)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            print("\n[ОШИБКА] 401 Unauthorized — WordPress отклонил логин/пароль.")
            print("  Проверьте в config/.env: WP_USERNAME и WP_APP_PASSWORD.")
            print("  Используйте «Пароль приложения» из WordPress: Профиль → Безопасность приложений.")
        raise
    link = result.get("link", "—")
    print(f"\n✅ Готово! Ссылка: {link}")
    if draft:
        print("   Статус: ЧЕРНОВИК (уберите --draft для публикации)")


if __name__ == "__main__":
    main()
