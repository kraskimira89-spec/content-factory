"""
Парсер каталога эфирных масел Gloryon.

Режимы:
- Авто: логин → каталог → обход масёл и вкладок (Selenium).
- Вместе (--together): ты открываешь страницы и вкладки, скрипт читает и сохраняет по Enter.

Запуск:
  python scripts/parse_gloryon_aroma.py --browser yandex
  python scripts/parse_gloryon_aroma.py --together   # интерактивный режим
"""
import argparse
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
load_dotenv(CONFIG_DIR / ".env")

OUTPUT_AROMA = PROJECT_ROOT / "output" / "aroma"
URL_LOGIN = "https://www.gloryon.com/ruRU/info/security/flogin"
URL_RUBRICATOR = "https://www.gloryon.com/ruRU/info/article/rubricator"
URL_CATALOG = "https://www.gloryon.com/site/catalog/10900"

KNOWN_OILS = [
    {"code": "00884", "name": "Пихтовая хвоя", "country": "Россия", "keyword": "Внутренняя выдержка и смелость"},
    {"code": "00863", "name": "Апельсин сладкий", "country": "Бразилия", "keyword": "Радость, стабилизатор эмоций"},
    {"code": "00851", "name": "Бергамот", "country": "Италия", "keyword": "Бактерицидное, тонизирующее"},
    {"code": "00865", "name": "Ваниль (масляный экстракт)", "country": "США", "keyword": "Нежность и доверие"},
    {"code": "00852", "name": "Герань", "country": "Египет", "keyword": "«Домашний доктор»"},
    {"code": "00853", "name": "Грейпфрут", "country": "Израиль", "keyword": "Витамин С, иммунитет"},
    {"code": "00854", "name": "Иланг-иланг", "country": "Мадагаскар", "keyword": "Афродизиак"},
    {"code": "00859", "name": "Лаванда", "country": "Болгария", "keyword": "Релакс души и тела"},
    {"code": "00861", "name": "Лимон", "country": "Испания", "keyword": "Безболезненная адаптация, перемены"},
    {"code": "00869", "name": "Можжевельник", "country": "Хорватия", "keyword": "Внутренняя чистота и здоровье"},
    {"code": "00862", "name": "Мята перечная", "country": "Индия", "keyword": "Эмоциональный баланс, уравновешенность"},
    {"code": "00868", "name": "Мандарин", "country": "Италия", "keyword": "Детство и творчество"},
    {"code": "00864", "name": "Пальмароза", "country": "Индия", "keyword": "Антидепрессант"},
    {"code": "00866", "name": "Петитгрейн", "country": "Парагвай", "keyword": "Масло победителей"},
    {"code": "00857", "name": "Розмарин", "country": "Германия", "keyword": "Стимуляция мозговой активности"},
    {"code": "00860", "name": "Чайное дерево", "country": "Германия", "keyword": "Щит, защитник положительных эмоций"},
    {"code": "00855", "name": "Кедровое дерево", "country": "Индия", "keyword": "Антисептик, болеутоляющее", "unavailable": True},
    {"code": "00858", "name": "Эвкалипт", "country": "Германия", "keyword": "Масло логики", "unavailable": True},
]

TAB_NAMES = ["Презентация", "Описание", "Состав", "Применение", "Мой SMM", "Истории"]


def _sanitize_filename(name: str) -> str:
    s = re.sub(r"[<>:\"|?*\\/]", "_", name)
    s = re.sub(r"\s+", "_", s).strip("_")[:80]
    return s or "product"


YANDEX_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
    Path(r"C:\Program Files (x86)\Yandex\YandexBrowser\Application\browser.exe"),
    Path(r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe"),
]

SCRIPT_DIR = Path(__file__).resolve().parent
def _yandex_driver_candidates() -> list[Path]:
    base = [SCRIPT_DIR / "drivers" / "yandexdriver.exe", SCRIPT_DIR / "yandexdriver.exe"]
    if p := os.getenv("YANDEX_DRIVER_PATH", "").strip():
        return [Path(p)] + base
    return base


def _find_yandex_browser() -> str | None:
    for p in YANDEX_PATHS:
        if p and p.exists():
            return str(p)
    return None


def _find_yandex_driver() -> str | None:
    """Путь к YandexDriver. Скачать: https://github.com/yandex/YandexDriver/releases"""
    for p in _yandex_driver_candidates():
        if p.exists():
            return str(p)
    return None


def create_driver(headless: bool = False, browser: str = "chrome") -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=ru")

    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("prefs", {"profile.default_content_setting_values.javascript": 1})

    service = None
    if browser.lower() == "yandex":
        yandex_exe = _find_yandex_browser()
        if yandex_exe:
            opts.binary_location = yandex_exe
        else:
            print("[WARN] Yandex Browser не найден, используем Chrome")

        driver_path = _find_yandex_driver()
        if driver_path:
            service = Service(executable_path=driver_path)
            print("[OK] YandexDriver:", driver_path)
        else:
            print("[WARN] YandexDriver не найден. Скачай yandexdriver.exe с https://github.com/yandex/YandexDriver/releases")
            print("       и положи в scripts/drivers/ или укажи YANDEX_DRIVER_PATH в config/.env")
            print("       Продолжаю с ChromeDriver (могут быть ошибки)...")

    if service is None and ChromeDriverManager:
        service = Service(ChromeDriverManager().install())

    if service:
        return webdriver.Chrome(service=service, options=opts)
    return webdriver.Chrome(options=opts)


def close_modal(driver) -> bool:
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'OK')]"))
        )
        btn.click()
        time.sleep(0.5)
        return True
    except Exception:
        pass
    try:
        overlay = driver.find_element(By.CSS_SELECTOR, "[class*='modal'], [class*='popup'], .dialog")
        overlay.find_element(By.XPATH, ".//button | .//a[contains(text(),'OK')]").click()
        return True
    except Exception:
        pass
    return False


def login_gloryon(driver) -> bool:
    """Логин на flogin: первое поле — логин, второе — пароль."""
    username = os.getenv("GLORYON_USERNAME", "").strip()
    password = os.getenv("GLORYON_PASSWORD", "").strip()
    if not username or not password:
        print("[ERROR] GLORYON_USERNAME и GLORYON_PASSWORD в config/.env")
        return False

    driver.get(URL_LOGIN)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    close_modal(driver)
    time.sleep(0.5)

    pwd_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
    text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
    if text_inputs:
        text_inputs[0].clear()
        text_inputs[0].send_keys(username)
    if pwd_inputs:
        pwd_inputs[0].clear()
        pwd_inputs[0].send_keys(password)
        pwd_inputs[0].send_keys(Keys.RETURN)
    else:
        visible = [i for i in driver.find_elements(By.TAG_NAME, "input") if i.is_displayed() and i.get_attribute("type") not in ("hidden", "submit")]
        if len(visible) >= 2:
            visible[1].clear()
            visible[1].send_keys(password)
            visible[1].send_keys(Keys.RETURN)
        else:
            driver.find_element(By.XPATH, "//*[contains(text(),'войти')] | //input[@type='submit'] | //button[@type='submit']").click()

    time.sleep(4)
    close_modal(driver)
    return True


def collect_oil_links_from_catalog(driver) -> list[dict]:
    """
    Собирает ссылки на масла со страницы каталога 10900.
    Если не нашли — возвращает KNOWN_OILS с url.
    """
    driver.get(URL_CATALOG)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(4)
    close_modal(driver)
    time.sleep(2)

    found = []
    links_seen = set()

    for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='catalog']"):
        href = (a.get_attribute("href") or "").rstrip("/")
        if not href or href in links_seen:
            continue
        for oil in KNOWN_OILS:
            if oil["code"] in href or oil["name"].lower() in (a.text or "").lower():
                links_seen.add(href)
                found.append({**oil, "url": href})
                break
        if len(found) >= len(KNOWN_OILS):
            break

    if found:
        return found

    return [{**o, "url": f"https://www.gloryon.com/site/catalog/10900/{o['code']}"} for o in KNOWN_OILS]


def _extract_tab_content(driver, tab_name: str) -> str | None:
    """Кликает по табу (в т.ч. скрытому) и извлекает текст."""
    for _ in range(2):
        try:
            for xpath in [
                f"//*[normalize-space(text())='{tab_name}']",
                f"//a[contains(text(),'{tab_name}')]",
                f"//button[contains(text(),'{tab_name}')]",
                f"//*[contains(@class,'tab') and contains(text(),'{tab_name}')]",
                f"//li//*[contains(text(),'{tab_name}')]",
            ]:
                try:
                    tabs = driver.find_elements(By.XPATH, xpath)
                    for t in tabs:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView();", t)
                            time.sleep(0.3)
                            if t.is_displayed() or t.get_attribute("aria-hidden") != "true":
                                t.click()
                                time.sleep(3)
                                break
                        except Exception:
                            continue
                except Exception:
                    continue

            for sel in [
                "[class*='tabpanel']:not([aria-hidden='true'])",
                "[class*='tab-content'] [class*='active']",
                "[class*='content']",
                "main",
                "article",
                ".product-description",
            ]:
                try:
                    for el in driver.find_elements(By.CSS_SELECTOR, sel):
                        if el.is_displayed():
                            txt = el.text.strip()
                            if len(txt) > 30:
                                return txt
                except Exception:
                    continue

            body = driver.find_element(By.TAG_NAME, "body")
            txt = body.text.strip()
            if len(txt) > 50:
                return txt[:5000]
        except Exception:
            time.sleep(0.5)
    return None


def scrape_oil_page(driver, url: str, oil: dict) -> dict:
    """Открывает страницу масла, кликает все табы и собирает контент."""
    result = {"presentation": None, "description": None, "composition": None, "application": None, "smm": None, "stories": None}

    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
        close_modal(driver)
        time.sleep(2)

        for tab in TAB_NAMES:
            key = tab.lower().replace(" ", "_").replace("мой_smm", "smm").replace("истории", "stories")
            content = _extract_tab_content(driver, tab)
            if content:
                result[key] = content
    except Exception as e:
        result["_error"] = str(e)
    return result


def merge_oil_md(file_path: Path, oil: dict, scraped: dict) -> str:
    """Дополняет .md новыми секциями."""
    existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    sections = [
        ("Презентация", scraped.get("presentation")),
        ("Описание", scraped.get("description")),
        ("Состав", scraped.get("composition")),
        ("Применение", scraped.get("application")),
        ("Мой SMM", scraped.get("smm")),
        ("Истории", scraped.get("stories")),
    ]
    new_parts = []
    for title, content in sections:
        if not content or len(content.strip()) < 10:
            continue
        if title in existing or f"### {title}" in existing or f"## {title}" in existing:
            continue
        new_parts.append(f"### {title}\n\n{content.strip()}")

    if not existing.strip():
        header = [
            f"# {oil['name']}",
            "",
            f"Код: {oil['code']} | Страна: {oil['country']} | {oil['keyword']}",
            "",
            f"[Gloryon]({oil.get('url', URL_CATALOG + '/' + oil['code'])})",
            "",
        ]
        body = "\n\n".join(new_parts) if new_parts else ""
        if scraped.get("_error"):
            body += f"\n\n*Ошибка: {scraped['_error']}*"
        return "\n".join(header) + "\n\n" + body

    if not new_parts:
        return existing.rstrip()
    return existing.rstrip() + "\n\n---\n\n## Дополнение\n\n" + "\n\n".join(new_parts)


def _read_current_page(driver) -> str:
    """Читает текст текущей страницы в браузере."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text.strip()
    except Exception:
        return ""


def run_together_mode(driver, oils: list[dict]) -> None:
    """
    Интерактивный режим: пользователь открывает страницы и вкладки,
    по Enter скрипт читает контент и сохраняет.
    """
    print("\n" + "=" * 50)
    print("РЕЖИМ ВМЕСТЕ")
    print("Ты открываешь страницы и вкладки в браузере.")
    print("Когда готово — нажми Enter в этом окне.")
    print("Скрипт прочитает страницу и скажет Дальше.")
    print("=" * 50)

    driver.get(URL_CATALOG)
    time.sleep(2)
    close_modal(driver)
    input("\nОткрой каталог 10900, залогинься. Готово? Enter... ")

    for i, oil in enumerate(oils, 1):
        print(f"\n--- Масло {i}/{len(oils)}: {oil['name']} ---")
        scraped = {}

        input(f"Открой страницу [{oil['name']}] в каталоге. Enter... ")

        tab_to_key = {"Презентация": "presentation", "Описание": "description", "Состав": "composition",
                      "Применение": "application", "Мой SMM": "smm", "Истории": "stories"}
        for tab in TAB_NAMES:
            key = tab_to_key.get(tab, tab.lower().replace(" ", "_"))
            input(f"  Вкладка [{tab}]. Готово? Enter... ")
            text = _read_current_page(driver)
            if text:
                scraped[key] = text
                print("    [OK] прочитано")
            else:
                print("    [пусто]")
            print("  Дальше.")

        md_path = OUTPUT_AROMA / (_sanitize_filename(oil["name"]) + ".md")
        merged = merge_oil_md(md_path, oil, scraped)
        md_path.write_text(merged, encoding="utf-8")
        print(f"  Сохранено: {md_path.name}\n")

    print("\n[OK] Все масла сохранены в output/aroma/")


def save_catalog_md() -> Path:
    OUTPUT_AROMA.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Каталог эфирных масел Gloris Aroma (10900)",
        "",
        f"Источник: {URL_CATALOG}",
        "",
        "| Код | Масло | Страна | Образ / ключевое слово |",
        "|-----|-------|--------|------------------------|",
    ]
    for o in KNOWN_OILS:
        kw = o["keyword"] + (" *(нет в наличии)*" if o.get("unavailable") else "")
        lines.append(f"| {o['code']} | {o['name']} | {o['country']} | {kw} |")
    lines.extend(["", "---", "", "Файлы: `output/aroma/{название}.md`"])
    catalog_path = OUTPUT_AROMA / "catalog_10900.md"
    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    return catalog_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-login", action="store_true", help="Пропустить логин (если уже залогинен)")
    parser.add_argument("--browser", default="yandex", choices=["chrome", "yandex"], help="Браузер: chrome или yandex (по умолч. yandex)")
    parser.add_argument("--together", action="store_true", help="Режим вместе: ты открываешь, скрипт читает по Enter")
    args = parser.parse_args()

    OUTPUT_AROMA.mkdir(parents=True, exist_ok=True)
    save_catalog_md()
    print("[OK] Каталог: catalog_10900.md")

    if args.catalog_only:
        return

    if args.together:
        oils = KNOWN_OILS[: args.limit] if args.limit > 0 else KNOWN_OILS
        driver = create_driver(headless=False, browser=args.browser)
        try:
            run_together_mode(driver, oils)
        finally:
            driver.quit()
        return

    if not args.no_login:
        if not os.getenv("GLORYON_USERNAME") or not os.getenv("GLORYON_PASSWORD"):
            print("[ERROR] Добавь GLORYON_USERNAME и GLORYON_PASSWORD в config/.env")
            return

    driver = None
    try:
        driver = create_driver(headless=args.headless, browser=args.browser)
        print(f"Браузер: {args.browser}")

        if not args.no_login:
            print("Логин...")
            if not login_gloryon(driver):
                return
            print("  OK")

        print("Каталог 10900...")
        oils = collect_oil_links_from_catalog(driver)
        if args.limit > 0:
            oils = oils[: args.limit]
        print(f"  Масёл: {len(oils)}")

        for i, oil in enumerate(oils, 1):
            fname = _sanitize_filename(oil["name"]) + ".md"
            md_path = OUTPUT_AROMA / fname
            url = oil.get("url", f"https://www.gloryon.com/site/catalog/10900/{oil['code']}")
            print(f"  [{i}/{len(oils)}] {oil['name']}...", end=" ", flush=True)
            scraped = scrape_oil_page(driver, url, oil)
            merged = merge_oil_md(md_path, oil, scraped)
            md_path.write_text(merged, encoding="utf-8")
            n = sum(1 for v in scraped.values() if v and not str(v).startswith("_"))
            print(f"ok sections={n}", flush=True)
            time.sleep(1.5)

        print("[OK] output/aroma/")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
