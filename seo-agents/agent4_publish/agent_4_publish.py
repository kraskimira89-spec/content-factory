import json
import os
import sys
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

# Публикующий агент обязан перед публикацией вызвать get_hero_image(post_id) и прикрепить как featured image
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
try:
    from scripts.shared_config import get_image_path_for_network, resolve_image_path
except ImportError:
    get_image_path_for_network = None  # type: ignore[assignment]
    resolve_image_path = None  # type: ignore[assignment]
try:
    from scripts.image_repository import get_hero_image, get_images, set_attachment_id
except ImportError:
    get_hero_image = None  # type: ignore[assignment]
    get_images = None  # type: ignore[assignment]
    set_attachment_id = None  # type: ignore[assignment]

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


# Связка agent8/agent9 → agent4: images-generated.json рядом с .md, имя {stem}.images-generated.json
def get_images_generated_path(md_path: Path) -> Path:
    """Путь к JSON с картинками от agent9 для данного поста (по конвенции: тот же каталог, stem.images-generated.json)."""
    return md_path.parent / (md_path.stem + ".images-generated.json")


def load_images_generated_for_md(md_path: Path) -> dict | None:
    """
    Читает images-generated.json для поста (от agent9).
    Возвращает {"images": [{"variants": {"site": {...}, "vk": {...}, ...}, "alt", ...}], "service_slug": "..."} или None.
    """
    path = get_images_generated_path(md_path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _get_site_image_path(image_rec: dict) -> str | None:
    """Путь к картинке для сайта (WordPress): site.hero, жёстко для пайплайна."""
    if get_image_path_for_network is not None:
        return get_image_path_for_network(image_rec, "site")  # variant hero по умолчанию
    variants = image_rec.get("variants") or {}
    site = variants.get("site")
    if isinstance(site, list) and site:
        for item in site:
            if item.get("name") == "hero":
                return item.get("image_path")
        return site[0].get("image_path")
    return image_rec.get("image_path") if isinstance(site, dict) else image_rec.get("image_path")


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


# Цвет заголовков в постах блога (как в теме: #24937a)
BLOG_HEADING_COLOR = "#24937a"


def apply_blog_heading_styles(html: str) -> str:
    """
    Для постов блога: зелёный цвет заголовков, SEO-иерархия (H1→H2, т.к. заголовок поста уже H1).
    Шрифт — из темы сайта (семантические теги h2, h3...).
    """
    # H1 в контенте поста → H2 (заголовок поста уже H1 у WP)
    html = re.sub(r"<h1(\s[^>]*)?>", r"<h2\1>", html, flags=re.IGNORECASE)
    html = re.sub(r"</h1>", "</h2>", html, flags=re.IGNORECASE)

    def add_color(match: re.Match) -> str:
        tag = match.group(0)
        if 'style=' in tag and 'color:' not in tag:
            return re.sub(r'(style=["\'])([^"\']*?)(["\'])', rf'\1\2; color: {BLOG_HEADING_COLOR}; font-family: sans-serif\3', tag, count=1)
        if 'style=' in tag and 'font-family:' not in tag:
            return re.sub(r'(style=["\'])([^"\']*?)(["\'])', rf'\1\2; font-family: sans-serif\3', tag, count=1)
        if 'style=' in tag:
            return tag  # уже есть color и font
        return tag[:-1] + f' style="color: {BLOG_HEADING_COLOR}; font-family: sans-serif">'

    for tag_name in ["h2", "h3", "h4", "h5", "h6"]:
        html = re.sub(rf"<{tag_name}(\s[^>]*)?>", add_color, html)
    return html


def _build_service_phrase_map() -> list[tuple[str, str]]:
    """(phrase, slug) из services, длинные фразы первыми (для корректной перелинковки)."""
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
    """
    Для постов блога: ключевые слова — жирным; первое упоминание услуги — ссылка на страницу.
    Перелинковка по названиям и алиасам из shared-config.services.
    """
    phrase_map = _build_service_phrase_map()
    if not phrase_map:
        return html

    # Разбиваем на теги и текст, чтобы не трогать атрибуты
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
                # Остальные вхождения — только жирное (сохраняем регистр из текста)
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                text = pattern.sub(lambda m: f"<strong>{m.group(0)}</strong>", text)
            else:
                # Первое вхождение — ссылка + жирное
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                link = f'<a href="{base_url}/uslugi/{slug}/"><strong>\\g<0></strong></a>'
                text = pattern.sub(link, text, count=1)
                linked.add(phrase)

        result.append(text)

    return "".join(result)


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


def upload_image_to_wp(
    wp_url: str, wp_user: str, wp_app_password: str, file_path: Path
) -> int:
    """
    Загружает файл в WordPress Media. Возвращает attachment ID.
    file_path — абсолютный путь к PNG/JPEG.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Файл картинки не найден: {file_path}")
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media"
    headers = _wp_headers(wp_user, wp_app_password, content_type=False)
    # WP ожидает multipart: поле file с именем файла
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg")}
        resp = _wp_request("POST", api_url, wp_user, wp_app_password, files=files, headers=headers, timeout=60)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Ошибка загрузки медиа: {resp.status_code}\n{resp.text}")
    data = resp.json()
    return int(data.get("id", 0))


def _get_attachment_source_url(
    wp_url: str, wp_user: str, wp_app_password: str, attachment_id: int
) -> str:
    """Возвращает source_url вложения для вставки в контент."""
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media/{attachment_id}"
    resp = _wp_request("GET", api_url, wp_user, wp_app_password)
    if resp.status_code != 200:
        return ""
    return resp.json().get("source_url", "")


def _resolve_image_url(
    wp_url: str, wp_user: str, wp_app_password: str, page_id: int, rec: dict
) -> tuple[int | None, str]:
    """
    По записи из индекса возвращает (attachment_id, source_url).
    Если есть wp_attachment_id — берём URL через API; иначе загружаем файл, обновляем индекс.
    """
    aid = rec.get("wp_attachment_id")
    if aid is not None:
        url = _get_attachment_source_url(wp_url, wp_user, wp_app_password, int(aid))
        return int(aid), url
    path_raw = rec.get("file_path")
    if not path_raw:
        return None, ""
    if Path(path_raw).is_absolute():
        abs_path = Path(path_raw)
    elif resolve_image_path is not None:
        abs_path = resolve_image_path(path_raw)
    else:
        abs_path = PROJECT_ROOT / path_raw
    if not abs_path.is_file():
        return None, ""
    try:
        aid = upload_image_to_wp(wp_url, wp_user, wp_app_password, abs_path)
        if set_attachment_id:
            set_attachment_id(str(page_id), rec.get("image_id", "img"), aid)
        url = _get_attachment_source_url(wp_url, wp_user, wp_app_password, aid)
        return aid, url
    except Exception:
        return None, ""


def _embed_images_in_content(content_html: str, images: list[dict]) -> str:
    """
    Вставляет блоки <figure><img></figure> после первого абзаца.
    images: список { "url": "...", "alt": "..." }.
    """
    if not images:
        return content_html
    block_parts = []
    for img in images:
        if not img.get("url"):
            continue
        url = img["url"].replace('"', "&quot;")
        alt = (img.get("alt") or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        block_parts.append(f'<figure><img src="{url}" alt="{alt}" /></figure>')
    block = "".join(block_parts)
    # Вставка после первого </p>
    pos = content_html.find("</p>")
    if pos != -1:
        insert_at = pos + len("</p>")
        return content_html[:insert_at] + block + content_html[insert_at:]
    return content_html + block


def _resolve_hero_attachment_id(
    wp_url: str, wp_user: str, wp_app_password: str, page_id: int, hero_record: dict | None
) -> int | None:
    """
    По записи hero из get_hero_image возвращает attachment ID для featured_media.
    Если в записи есть wp_attachment_id — возвращает его; иначе загружает file_path в WP Media,
    обновляет индекс и возвращает новый id.
    """
    if not hero_record or get_hero_image is None or set_attachment_id is None:
        return None
    aid = hero_record.get("wp_attachment_id")
    if aid is not None:
        return int(aid)
    path_raw = hero_record.get("file_path")
    if not path_raw:
        return None
    if Path(path_raw).is_absolute():
        abs_path = Path(path_raw)
    elif resolve_image_path is not None:
        abs_path = resolve_image_path(path_raw)
    else:
        abs_path = PROJECT_ROOT / path_raw
    if not abs_path.is_file():
        print(f"  ⚠️ Hero-картинка не найдена по пути: {abs_path} (TODO: загрузить в WP)")
        return None
    try:
        aid = upload_image_to_wp(wp_url, wp_user, wp_app_password, abs_path)
        set_attachment_id(str(page_id), hero_record.get("image_id", "hero"), aid)
        print(f"  📷 Hero-картинка загружена в медиа: attachment_id={aid}")
        return aid
    except Exception as e:
        print(f"  ⚠️ Не удалось загрузить hero-картинку: {e}")
        return None


def update_page_content(
    wp_url: str,
    wp_user: str,
    wp_app_password: str,
    page_id: int,
    content_html: str,
    *,
    status: str | None = None,
    featured_media: int | None = None,
) -> dict:
    """
    Обновляет post_content существующей WordPress-страницы.
    status: если задан (draft, publish, private) — обновляет и статус страницы.
    featured_media: ID вложения для миниатюры страницы.
    """
    api_url = f"{wp_url}/wp-json/wp/v2/pages/{page_id}"
    payload: dict = {"content": content_html}
    if status:
        payload["status"] = status
    if featured_media is not None:
        payload["featured_media"] = featured_media
    resp = _wp_request("POST", api_url, wp_user, wp_app_password, json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Ошибка обновления страницы {page_id}: {resp.status_code}\n{resp.text}"
        )
    return resp.json()


def set_page_featured_media(
    wp_url: str, wp_user: str, wp_app_password: str, page_id: int, attachment_id: int
) -> dict:
    """Устанавливает только featured_media для страницы (PATCH)."""
    api_url = f"{wp_url}/wp-json/wp/v2/pages/{page_id}"
    resp = _wp_request("POST", api_url, wp_user, wp_app_password, json={"featured_media": attachment_id})
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Ошибка установки featured_media: {resp.status_code}\n{resp.text}")
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

    # Картинки от agent8/agent9 (images-generated.json рядом с .md; для сайта — variants.site)
    images_generated = load_images_generated_for_md(md_path)
    if images_generated:
        imgs = images_generated.get("images", [])
        if imgs:
            first = imgs[0]
            site_path = _get_site_image_path(first)
            print(f"[agent4] Найден images-generated.json: featured_media будет: {site_path or '—'} (alt: {first.get('alt', '')})")
            for i, rec in enumerate(imgs[1:], start=2):
                print(f"[agent4]   в контент img[{i}]: {_get_site_image_path(rec) or '—'}")
        else:
            print("[agent4] images-generated.json пустой (images: [])")
    else:
        print("[agent4] images-generated.json не найден — featured/embed по текущему индексу (get_hero_image, get_images)")

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
                content_no_faq = _strip_faq_block_from_html(content_html)
                content_no_faq = _strip_indications_block_from_html(content_no_faq)
                hero_attachment_id = None
                images_to_embed: list[dict] = []
                if get_hero_image and get_images:
                    hero_record = get_hero_image(str(page["id"]))
                    hero_attachment_id = _resolve_hero_attachment_id(
                        wp_url, wp_user, wp_app_password, page["id"], hero_record
                    )
                    # Остальные картинки — в контент (первая с purpose hero уже как featured)
                    all_images = get_images(str(page["id"]))
                    hero_id = hero_record.get("image_id") if hero_record else None
                    for rec in all_images:
                        if rec.get("image_id") == hero_id:
                            continue
                        _aid, url = _resolve_image_url(
                            wp_url, wp_user, wp_app_password, page["id"], rec
                        )
                        if url:
                            images_to_embed.append({
                                "url": url,
                                "alt": rec.get("alt") or rec.get("purpose") or rec.get("image_id", ""),
                            })
                if images_to_embed:
                    content_no_faq = _embed_images_in_content(content_no_faq, images_to_embed)
                print(f"Обновляю post_content страницы ({status_msg})...")
                result = update_page_content(
                    wp_url, wp_user, wp_app_password, page["id"], content_no_faq,
                    status="draft" if draft else None,
                    featured_media=hero_attachment_id,
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
                if page_id and get_hero_image:
                    hero_record = get_hero_image(str(page_id))
                    hero_attachment_id = _resolve_hero_attachment_id(
                        wp_url, wp_user, wp_app_password, page_id, hero_record
                    )
                    if hero_attachment_id is not None:
                        set_page_featured_media(wp_url, wp_user, wp_app_password, page_id, hero_attachment_id)
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

    # Стили заголовков, жирные ключи, перелинковка + кнопки в конце
    content_html = apply_blog_heading_styles(content_html)
    base_url = wp_url.rstrip("/")
    content_html = apply_blog_keywords_and_links(content_html, base_url)
    cta_buttons = (
        '<p style="margin-top: 2em; display: flex; gap: 1em; flex-wrap: wrap;">'
        f'<a href="{base_url}/blog/" style="display: inline-block; padding: 0.6em 1.2em; '
        'background: #24937a; color: #fff; text-decoration: none; border-radius: 4px; border: 1px solid #1a6b5a;">Далее</a>'
        f'<a href="{base_url}/#callback" style="display: inline-block; padding: 0.6em 1.2em; '
        'background: #ff8800; color: #fff; text-decoration: none; border-radius: 4px;">Записаться</a>'
        '</p>'
    )
    post_content = (content_html + cta_buttons).strip()

    result = publish_post(
        wp_url=wp_url,
        wp_user=wp_user,
        wp_app_password=wp_app_password,
        title=title,
        content_html=post_content,
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
