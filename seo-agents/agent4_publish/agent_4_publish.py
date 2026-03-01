import json
import os
import base64
import glob
import re
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import markdown
from dotenv import load_dotenv

# === Настройки путей ===

# Базовая директория проекта seo-agents (папка, где лежит .env и агенты)
BASE_DIR = Path(__file__).resolve().parents[1]  # .../seo-agents
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../content-factory

# Папка, куда Агент 3 кладёт Markdown-страницы
OUTPUT_DIR = PROJECT_ROOT / "output"

# === Загрузка контракта ===

_CONFIG = json.loads((PROJECT_ROOT / "config" / "shared-config.json").read_text("utf-8"))

# === HTTP-сессия с автоматическими повторами ===

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0


def _create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=["GET", "POST", "PUT"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _create_session()


def _wp_headers(wp_user: str, wp_app_password: str, content_type: bool = False) -> dict:
    token = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    h = {"Authorization": f"Basic {token}"}
    if content_type:
        h["Content-Type"] = "application/json"
    return h


def _wp_request(method: str, url: str, wp_user: str, wp_app_password: str,
                retries: int = MAX_RETRIES, **kwargs) -> requests.Response:
    """HTTP-запрос к WP REST API с retry и обработкой ошибок."""
    headers = _wp_headers(wp_user, wp_app_password, content_type="json" in kwargs)
    kwargs.setdefault("headers", headers)
    kwargs.setdefault("timeout", 30)

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = _session.request(method, url, **kwargs)
            if resp.status_code == 401:
                raise RuntimeError("❌ Авторизация WP не прошла (401). Проверьте WP_USERNAME / WP_APP_PASSWORD")
            if resp.status_code == 403:
                raise RuntimeError("❌ Нет прав (403). Пользователю нужна capability edit_posts / edit_pages")
            return resp
        except requests.exceptions.ConnectionError as e:
            last_err = e
            print(f"  ⚠️ Сетевая ошибка (попытка {attempt}/{retries}): {e}")
        except requests.exceptions.Timeout as e:
            last_err = e
            print(f"  ⚠️ Таймаут (попытка {attempt}/{retries})")
        if attempt < retries:
            wait = RETRY_BACKOFF * attempt
            print(f"  ⏳ Повтор через {wait:.0f} с...")
            time.sleep(wait)

    raise RuntimeError(f"❌ Все {retries} попыток неудачны: {last_err}")


# === Рубрики блога (из shared-config.json) ===

RUBRICS = tuple(
    {"key": k, "title": v["title"], "keywords": v.get("keywords", "")}
    for k, v in _CONFIG["rubrics"].items()
    if v.get("keywords")
)


# === Работа с .env ===

def load_env():
    """Читает настройки WordPress из .env без изменения пароля."""
    env_path = PROJECT_ROOT / "config" / ".env"
    if not env_path.exists():
        raise RuntimeError(f".env не найден по пути: {env_path}")

    load_dotenv(env_path)

    wp_url = os.getenv("WP_URL")
    wp_user = os.getenv("WP_USERNAME")
    wp_app_password = os.getenv("WP_APP_PASSWORD")

    if not wp_url or not wp_user or not wp_app_password:
        raise RuntimeError(
            "Не заданы WP_URL, WP_USERNAME или WP_APP_PASSWORD в .env"
        )

    # Убираем только слэш в конце URL
    wp_url = wp_url.rstrip("/")

    # Пароль оставляем строго как в WordPress (включая пробелы)
    return wp_url, wp_user, wp_app_password


def get_rubric_category_ids():
    """
    Читает из .env ID категорий WP для рубрик.
    Ключи: WP_CAT_HEALTH_FITNESS, WP_CAT_RELAX_MASSAGE, WP_CAT_NUTRITION_LIFESTYLE.
    """
    load_dotenv(PROJECT_ROOT / "config" / ".env")
    ids = {}
    for r in RUBRICS:
        val = os.getenv(f"WP_CAT_{r['key'].upper()}", "").strip()
        if val.isdigit():
            ids[r["key"]] = int(val)
    return ids


def load_metadata_for_md(md_path: Path) -> dict:
    """
    Читает метаданные для выбранного .md: файл с тем же именем и суффиксом .meta.json.
    Формат: {"rubric_key": "client_stories", "content_type": "case"}.
    Возвращает пустой dict, если файла нет или JSON невалиден.
    """
    meta_path = md_path.with_suffix(md_path.suffix + ".meta.json")
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def select_rubric(title: str, content_text: str) -> str:
    """
    Выбирает одну из рубрик по заголовку и тексту (ключевые слова).
    Возвращает ключ рубрики (health_fitness | relax_massage | nutrition_lifestyle | client_stories | ai_health).
    """
    text = f"{title}\n{content_text}".lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    scores = []
    for r in RUBRICS:
        score = sum(1 for w in r["keywords"].split() if w in text)
        scores.append((r["key"], score))
    best = max(scores, key=lambda x: x[1])
    return best[0] if best[1] > 0 else RUBRICS[0]["key"]


# === Работа с файлами Markdown от Агента 3 ===

def get_latest_md_file():
    """Возвращает путь к последнему .md файлу вида *_page_*.md из output."""
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Папка с output не найдена: {OUTPUT_DIR}")

    pattern = str(OUTPUT_DIR / "*_page_*.md")
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if not files:
        raise FileNotFoundError(f"В {OUTPUT_DIR} нет файлов по шаблону *_page_*.md")
    return Path(files[-1])


def get_md_file_for_slug(slug: str) -> Path:
    """
    Ищет файл *_page_*.md, в имени которого услуга соответствует slug.
    Формат имени: {timestamp}_page_{услуга}_{город}.md
    """
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Папка с output не найдена: {OUTPUT_DIR}")

    pattern = str(OUTPUT_DIR / "*_page_*.md")
    candidates = []
    for p in glob.glob(pattern):
        path = Path(p)
        if "approved" in path.stem.lower():
            continue
        service_name, city = parse_service_and_city_from_filename(path)
        if service_name:
            resolved = resolve_page_slug(service_name)
            if resolved == slug:
                candidates.append(path)

    if not candidates:
        raise FileNotFoundError(
            f"Нет файла для услуги со slug «{slug}». "
            f"Ожидается имя вида *_page_Прессотерапия_Ноябрьск.md (для pressoterapiya)."
        )
    # Берём самый новый из подходящих
    return max(candidates, key=lambda p: os.path.getmtime(p))


def parse_service_and_city_from_filename(md_path: Path) -> tuple[str | None, str | None]:
    """
    Ждём имя вида: {timestamp}_page_{услуга}_{город}.md
    Возвращает (service_name, city). Файлы с «approved» в имени (от Editor) не разбираем — (None, None).
    """
    name = md_path.stem
    parts = name.split("_page_")
    if len(parts) != 2:
        return None, None

    tail = parts[1]
    if "approved" in tail.lower():
        return None, None

    tail_parts = tail.split("_")
    if len(tail_parts) < 2:
        return None, None

    city = tail_parts[-1]
    service = " ".join(tail_parts[:-1])
    return service, city


def _strip_citation_markers(text: str) -> str:
    """Удаляет маркеры цитирования [1], [2], [1][2] и т.п."""
    return re.sub(r"\[\d+\]", "", text)


def _strip_faq_block_from_html(html: str) -> str:
    """
    Удаляет блок «Часто задаваемые вопросы» из HTML.
    FAQ отображается только шаблонным аккордеоном из service_data — дубли в post_content убираем.
    """
    for pattern in (
        re.compile(
            r'<h2[^>]*>\s*Часто задаваемые вопросы\s*</h2>.*?(?=<h2|\Z)',
            re.DOTALL | re.IGNORECASE,
        ),
        re.compile(
            r'<h3[^>]*>\s*FAQ\s*</h3>.*?(?=<h2|<h3|\Z)',
            re.DOTALL | re.IGNORECASE,
        ),
    ):
        html = pattern.sub("", html)
    return html.strip()


def _strip_indications_block_from_html(html: str) -> str:
    """
    Удаляет блок «Показания и противопоказания» из HTML.
    Эти блоки отображаются шаблоном из service_data — дубли в post_content убираем.
    """
    pattern = re.compile(
        r'<h2[^>]*>\s*Показания и противопоказания\s*</h2>.*?(?=<h2|\Z)',
        re.DOTALL | re.IGNORECASE,
    )
    return pattern.sub("", html).strip()


def parse_markdown(md_text: str):
    """
    Берёт Markdown:
    - первая строка '# Заголовок' → title
    - остальное → body, конвертирует в HTML
    """
    lines = md_text.splitlines()
    title = "Без заголовка"
    body_lines = lines

    if lines and lines[0].startswith("# "):
        title = _strip_citation_markers(lines[0][2:].strip())
        body_lines = lines[1:]

    body_md = "\n".join(body_lines).strip()
    body_md = _strip_citation_markers(body_md)

    # Markdown → HTML с поддержкой таблиц/списков
    body_html = markdown.markdown(
        body_md,
        extensions=["extra", "tables", "sane_lists"]
    )

    return title, body_html


# === Работа со страницами услуг (pages) ===


def find_page_by_slug(
    wp_url: str, wp_user: str, wp_app_password: str, slug: str
) -> dict | None:
    """
    Ищет WordPress-страницу (page) по slug.
    Возвращает dict с id, title, link, status или None.
    """
    api_url = f"{wp_url}/wp-json/wp/v2/pages"
    resp = _wp_request(
        "GET", api_url, wp_user, wp_app_password,
        params={"slug": slug, "status": "publish,draft,private", "per_page": 1},
    )
    if resp.status_code != 200:
        return None

    pages = resp.json()
    if not pages:
        return None

    p = pages[0]
    return {
        "id": p["id"],
        "title": p["title"]["rendered"],
        "link": p["link"],
        "status": p["status"],
    }


def create_page(
    wp_url: str,
    wp_user: str,
    wp_app_password: str,
    title: str,
    content_html: str,
    slug: str,
    *,
    status: str = "draft",
    parent_slug: str = "uslugi",
) -> dict:
    """
    Создаёт новую WordPress-страницу (page).
    parent_slug: slug родительской страницы (по умолчанию «uslugi» для /uslugi/{slug}/).
    """
    parent_id = 0
    if parent_slug:
        parent_page = find_page_by_slug(wp_url, wp_user, wp_app_password, parent_slug)
        if parent_page:
            parent_id = parent_page["id"]

    api_url = f"{wp_url}/wp-json/wp/v2/pages"
    payload = {
        "title": title,
        "content": content_html,
        "slug": slug,
        "status": status,
        "parent": parent_id,
    }
    resp = _wp_request("POST", api_url, wp_user, wp_app_password, json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Ошибка создания страницы: {resp.status_code}\n{resp.text}"
        )
    return resp.json()


def update_page_content(
    wp_url: str,
    wp_user: str,
    wp_app_password: str,
    page_id: int,
    content_html: str,
    *,
    status: str | None = None,
) -> dict:
    """
    Обновляет post_content существующей WordPress-страницы.
    status: если задан (draft, publish, private) — обновляет и статус страницы.
    """
    api_url = f"{wp_url}/wp-json/wp/v2/pages/{page_id}"
    payload: dict = {"content": content_html}
    if status:
        payload["status"] = status
    resp = _wp_request("POST", api_url, wp_user, wp_app_password, json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Ошибка обновления страницы {page_id}: {resp.status_code}\n{resp.text}"
        )
    return resp.json()


# Маппинг: имя файла (service) → slug WordPress-страницы (из shared-config.json)
SERVICE_SLUG_MAP: dict[str, str] = {}
for _slug, _svc in _CONFIG["services"].items():
    SERVICE_SLUG_MAP[_svc["name"].lower()] = _slug
    for _alias in _svc.get("aliases", []):
        SERVICE_SLUG_MAP[_alias.lower()] = _slug


def resolve_page_slug(service_name: str) -> str | None:
    """
    По имени услуги возвращает slug страницы WordPress.
    Ищет в SERVICE_SLUG_MAP (нечувствительно к регистру).
    """
    key = service_name.strip().lower()
    return SERVICE_SLUG_MAP.get(key)


# === Публикация в WordPress (запись в блоге) ===


def get_or_create_tag(
    wp_url: str, wp_user: str, wp_app_password: str, name: str
) -> int | None:
    """
    Ищет тег по имени (GET с search), если нет — создаёт (POST).
    Возвращает ID тега или None при пустом name.
    """
    if not name:
        return None

    tags_url = f"{wp_url}/wp-json/wp/v2/tags"
    resp = _wp_request("GET", tags_url, wp_user, wp_app_password, params={"search": name})
    if resp.status_code == 200:
        for t in resp.json():
            if t.get("name") == name:
                return t.get("id")

    resp = _wp_request("POST", tags_url, wp_user, wp_app_password, json={"name": name})
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Не удалось создать тег '{name}': {resp.status_code}\n{resp.text}"
        )
    return resp.json().get("id")


def publish_post(
    wp_url: str,
    wp_user: str,
    wp_app_password: str,
    title: str,
    content_html: str,
    status: str = "draft",
    categories: list[int] | None = None,
    tags: list[int] | None = None,
):
    """
    Публикует пост в WordPress через REST API.
    categories и tags — списки ID категорий и тегов WP.
    """
    api_url = f"{wp_url}/wp-json/wp/v2/posts"
    data = {"title": title, "content": content_html, "status": status}
    if categories:
        data["categories"] = categories
    if tags:
        data["tags"] = tags

    resp = _wp_request("POST", api_url, wp_user, wp_app_password, json=data)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Ошибка публикации: {resp.status_code}\nТело ответа: {resp.text}"
        )
    return resp.json()


# === Точка входа Агента 4 ===

def main(
    slug_filter: str | None = None,
    draft: bool = False,
    as_post: bool = False,
    both: bool = False,
):
    """as_post: только пост в блог, игнорировать страницу. both: страница + пост."""
    print("=== Агент 4: публикация в WordPress ===")

    wp_url, wp_user, wp_app_password = load_env()
    print(f"WP_URL: {wp_url}")
    print(f"WP_USERNAME: {wp_user}")

    if slug_filter:
        md_path = get_md_file_for_slug(slug_filter)
        print(f"Используется файл (по slug «{slug_filter}»): {md_path}")
    else:
        md_path = get_latest_md_file()
        print(f"Используется файл: {md_path}")

    service_name, city = parse_service_and_city_from_filename(md_path)
    print(f"Услуга: {service_name or '—'}, город: {city or '—'}")

    md_text = md_path.read_text(encoding="utf-8")
    title, content_html = parse_markdown(md_text)
    print(f"Заголовок из Markdown: {title}")

    meta = load_metadata_for_md(md_path)

    # --- Режим обновления/создания страницы услуги ---
    # as_post: пропускаем страницу, сразу идём в пост. both: страница + пост.
    skip_page = as_post
    do_both = both

    if service_name and not skip_page:
        slug = resolve_page_slug(service_name)
        if slug:
            page = find_page_by_slug(wp_url, wp_user, wp_app_password, slug)
            if page:
                print(f"Найдена страница услуги: «{page['title']}» (ID={page['id']}, slug={slug})")
                status_msg = "черновик" if draft else "публикация"
                print(f"Обновляю post_content страницы ({status_msg})...")
                content_no_faq = _strip_faq_block_from_html(content_html)
                content_no_faq = _strip_indications_block_from_html(content_no_faq)
                result = update_page_content(
                    wp_url, wp_user, wp_app_password, page["id"], content_no_faq,
                    status="draft" if draft else None,
                )
                print(f"✅ Страница обновлена: ID={page['id']}, link={page['link']}" + (" (черновик)" if draft else ""))
                _log_to_db(meta, result)
                if not do_both:
                    return

            else:
                print(f"Страница со slug «{slug}» не найдена — создаю новую страницу.")
                content_no_faq = _strip_faq_block_from_html(content_html)
                content_no_faq = _strip_indications_block_from_html(content_no_faq)
                result = create_page(
                    wp_url, wp_user, wp_app_password,
                    title=title,
                    content_html=content_no_faq,
                    slug=slug,
                    status="draft" if draft else "publish",
                    parent_slug="uslugi",
                )
                page_id = result.get("id")
                link = result.get("link", "")
                print(f"[OK] Страница создана: ID={page_id}, link={link}" + (" (черновик)" if draft else ""))
                _log_to_db(meta, result)
                if not do_both:
                    return
        elif not do_both:
            print(f"Slug для услуги «{service_name}» не найден в маппинге — создаю пост в блог.")

    if as_post:
        print("Режим --as-post: создаю запись в блог.")

    # --- Режим создания поста в блог ---
    categories = None
    tags_ids = []

    if service_name or city:
        load_dotenv(PROJECT_ROOT / "config" / ".env")
        services_cat = os.getenv("WP_CAT_SERVICES", "").strip()
        services_category_id = int(services_cat) if services_cat.isdigit() else None
        if services_category_id is not None:
            categories = [services_category_id]
            print(f"Рубрика: Услуги (ID={services_category_id})")
        else:
            print("(WP_CAT_SERVICES не задан в .env — пост без категории)")

        if service_name:
            tid = get_or_create_tag(wp_url, wp_user, wp_app_password, service_name)
            if tid:
                tags_ids.append(tid)
        if city:
            tid = get_or_create_tag(wp_url, wp_user, wp_app_password, city)
            if tid:
                tags_ids.append(tid)
        if tags_ids:
            print(f"Теги: {service_name or ''}, {city or ''} (ID: {tags_ids})")
    else:
        rubric_keys = {r["key"] for r in RUBRICS}
        if meta.get("rubric_key") in rubric_keys:
            rubric_key = meta["rubric_key"]
            rubric_title = next(r["title"] for r in RUBRICS if r["key"] == rubric_key)
            print(f"Рубрика из метаданных: {rubric_title}")
        else:
            rubric_key = select_rubric(title, md_text)
            rubric_title = next(r["title"] for r in RUBRICS if r["key"] == rubric_key)
            print(f"Рубрика по содержанию: {rubric_title}")

        category_ids = get_rubric_category_ids()
        categories = [category_ids[rubric_key]] if rubric_key in category_ids else None
        if not categories:
            print("(ID категории для этой рубрики не заданы в .env — пост без категории)")

    result = publish_post(
        wp_url=wp_url,
        wp_user=wp_user,
        wp_app_password=wp_app_password,
        title=title,
        content_html=content_html,
        status="draft",
        categories=categories,
        tags=tags_ids if tags_ids else None,
    )

    post_id = result.get("id")
    link = result.get("link")
    print(f"✅ Запись создана: ID={post_id}, link={link}")

    _log_to_db(meta, result)


def _log_to_db(meta: dict, wp_result: dict):
    """Записывает факт публикации в БД (publishing_log) если content_item_id есть в мета."""
    content_item_id = meta.get("content_item_id") if isinstance(meta.get("content_item_id"), int) else None
    if not content_item_id:
        return
    try:
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from db import get_connection, is_available
        if not is_available():
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM channels WHERE name = 'blog' LIMIT 1")
            ch = cur.fetchone()
            channel_id = ch["id"] if ch else None
            post_id = str(wp_result.get("id", ""))
            link = wp_result.get("link", "")
            cur.execute(
                """INSERT INTO publishing_log
                   (content_item_id, channel_id, platform, external_id, url, published_at, status, response_raw)
                   VALUES (%s, %s, 'wordpress', %s, %s, now(), 'success', %s)""",
                (content_item_id, channel_id, post_id, link, json.dumps(wp_result)),
            )
            cur.execute(
                "UPDATE content_items SET status = 'published', updated_at = now() WHERE id = %s",
                (content_item_id,),
            )
            conn.commit()
            print("(Запись в БД: publishing_log, status=published)")
        finally:
            conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent 4: публикация в WordPress")
    parser.add_argument(
        "slug",
        nargs="?",
        default=None,
        help="Slug услуги (например, pressoterapiya). Без аргумента — последний файл из output",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Сохранить страницу как черновик (для проверки перед публикацией)",
    )
    parser.add_argument(
        "--as-post",
        action="store_true",
        help="Только пост в блог, без страницы под /uslugi/",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Страница + пост в блог (дублирование контента)",
    )
    args = parser.parse_args()
    main(
        slug_filter=args.slug,
        draft=args.draft,
        as_post=args.as_post,
        both=args.both,
    )
