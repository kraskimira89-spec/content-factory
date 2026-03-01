"""
Agent 7: manual_to_publish — мост от materials/pages_manual к output и WordPress.

Шаги:
1. Читает отредактированный .md из materials/pages_manual/{slug}.md
2. Копирует в output/, перезаписывая существующий *_page_*.md
3. Запускает agent4 — сохраняет страницу в WordPress как ЧЕРНОВИК (не публикует)
4. Парсит FAQ из .md и отправляет в service-data (REST API)
5. Выводит чек-лист для проверки перед публикацией

Использование:
  python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya
  python seo-agents/agent7_manual_publish/agent_7_manual_publish.py solyanaya-komnata
  python seo-agents/agent7_manual_publish/agent_7_manual_publish.py pressoterapiya --publish  # сразу опубликовать
"""

import base64
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Фикс кодировки на Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# --- Пути ---

_CURRENT = Path(__file__).resolve().parent
_AGENTS_DIR = _CURRENT.parent
PROJECT_ROOT = _AGENTS_DIR.parent

MANUAL_DIR = PROJECT_ROOT / "materials" / "pages_manual"
OUTPUT_DIR = PROJECT_ROOT / "output"

_CONFIG = json.loads((PROJECT_ROOT / "config" / "shared-config.json").read_text("utf-8"))

# Маппинг slug → имя услуги (для поиска файла в output)
SLUG_TO_NAME: dict[str, str] = {
    slug: svc["name"] for slug, svc in _CONFIG["services"].items()
}

DEFAULT_CITY = "Ноябрьск"


def get_manual_path(slug: str) -> Path:
    """Путь к ручному файлу materials/pages_manual/{slug}.md"""
    path = MANUAL_DIR / f"{slug}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"Файл не найден: {path}\n"
            f"Создайте его или проверьте slug (например, pressoterapiya, solyanaya-komnata)"
        )
    return path


def find_output_file(slug: str) -> Path:
    """
    Находит в output/ файл *_page_{услуга}_{город}.md для данного slug.
    """
    if slug not in SLUG_TO_NAME:
        raise ValueError(
            f"Неизвестный slug «{slug}». "
            f"Доступны: {', '.join(SLUG_TO_NAME.keys())}"
        )

    service_name = SLUG_TO_NAME[slug]
    # "Соляная комната" → "Соляная_комната"
    service_part = service_name.replace(" ", "_")
    pattern = f"*_page_{service_part}_{DEFAULT_CITY}.md"

    candidates = list(OUTPUT_DIR.glob(pattern))
    candidates = [p for p in candidates if "approved" not in p.stem.lower()]

    if not candidates:
        raise FileNotFoundError(
            f"В {OUTPUT_DIR} нет файла вида {pattern}. "
            f"Создайте его (скопируйте любой *_page_*.md и переименуйте) или запустите agent3."
        )

    return max(candidates, key=lambda p: os.path.getmtime(p))


def copy_manual_to_output(slug: str) -> Path:
    """
    Копирует materials/pages_manual/{slug}.md в output, перезаписывая существующий файл.
    Возвращает путь к обновлённому файлу в output.
    """
    manual_path = get_manual_path(slug)
    output_path = find_output_file(slug)

    content = manual_path.read_text(encoding="utf-8")
    output_path.write_text(content, encoding="utf-8")

    return output_path


def run_agent4(slug: str, draft: bool = True) -> int:
    """Запускает agent4. draft=True — сохраняет как черновик для проверки."""
    agent4_script = _AGENTS_DIR / "agent4_publish" / "agent_4_publish.py"
    if not agent4_script.is_file():
        raise FileNotFoundError(f"Agent4 не найден: {agent4_script}")

    cmd = [sys.executable, str(agent4_script), slug]
    if draft:
        cmd.append("--draft")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode


def _load_wp_auth() -> tuple[str, str, str]:
    """WP_URL, WP_USERNAME, WP_APP_PASSWORD из config/.env."""
    load_dotenv(PROJECT_ROOT / "config" / ".env")
    wp_url = (os.getenv("WP_URL") or "").rstrip("/")
    wp_user = os.getenv("WP_USERNAME", "")
    wp_pass = os.getenv("WP_APP_PASSWORD", "")
    if not all([wp_url, wp_user, wp_pass]):
        raise RuntimeError("WP_URL / WP_USERNAME / WP_APP_PASSWORD не заданы в config/.env")
    return wp_url, wp_user, wp_pass


def deploy_faq_to_service_data(slug: str, faq: list[dict]) -> bool:
    """POST faq в /wp-json/entuziastov75/v1/service-data/{slug}. Возвращает True при успехе."""
    if not faq:
        return True
    wp_url, wp_user, wp_pass = _load_wp_auth()
    endpoint = _CONFIG["endpoints"]["service_data"]["path"].replace("{slug}", slug)
    url = f"{wp_url}{endpoint}"
    token = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    try:
        resp = requests.post(
            url,
            json={"faq": faq},
            headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
            timeout=30,
        )
        return resp.status_code in (200, 201)
    except requests.RequestException:
        return False


def _print_verification_checklist(slug: str) -> None:
    """Выводит чек-лист проверки перед публикацией."""
    load_dotenv(PROJECT_ROOT / "config" / ".env")
    wp_url = (os.getenv("WP_URL") or "").rstrip("/")
    preview_url = f"{wp_url}/wp-admin/edit.php?post_type=page" if wp_url else ""
    print(f"""
✅ Страница сохранена как ЧЕРНОВИК. Проверьте перед публикацией:

📋 Чек-лист:
  • Логика текста: структура блоков, последовательность, призывы
  • Отсутствие дублей: FAQ, показания/противопоказания только из шаблона
  • Соответствие промптам: простой язык, ощущения, метафора, без крика

🌐 Черновик в админке: {preview_url}
   Найдите страницу «{slug}» → просмотр → проверьте → опубликуйте вручную.
""")


def main(slug: str, publish: bool = False) -> None:
    print("=== Agent 7: manual → output → WordPress ===\n")

    # 1. Копируем
    output_path = copy_manual_to_output(slug)
    print(f"✅ Файл {output_path.relative_to(PROJECT_ROOT)} обновлён из materials/pages_manual/{slug}.md\n")

    # 2. Запускаем agent4 (по умолчанию — черновик)
    draft_mode = not publish
    print("Запуск agent4..." + (" (черновик)" if draft_mode else " (публикация)"))
    returncode = run_agent4(slug, draft=draft_mode)

    if returncode == 0:
        # 3. Парсим FAQ из ручного файла и отправляем в service-data
        manual_path = get_manual_path(slug)
        faq_script = PROJECT_ROOT / "scripts" / "faq_parser.py"
        faq = []
        if faq_script.is_file():
            try:
                spec = importlib.util.spec_from_file_location("faq_parser", faq_script)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                faq = mod.parse_faq_from_file(manual_path)
                if faq:
                    if deploy_faq_to_service_data(slug, faq):
                        print(f"✅ FAQ обновлён в service-data ({len(faq)} вопросов)")
                    else:
                        print("⚠️ FAQ не отправлен в service-data (проверьте WP_* в .env)")
            except Exception:
                pass

        if draft_mode:
            _print_verification_checklist(slug)
        else:
            print(f"\n✅ Готово. Страница опубликована: /uslugi/{slug}/")
    else:
        print(f"\n⚠️ Agent4 завершился с кодом {returncode}. Проверьте вывод выше.")
        sys.exit(returncode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent 7: скопировать ручной текст в output и опубликовать через agent4"
    )
    parser.add_argument(
        "slug",
        help="Slug услуги (pressoterapiya, solyanaya-komnata и т.д.)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Сразу опубликовать (без черновика). По умолчанию — сохранить как черновик.",
    )
    args = parser.parse_args()
    main(args.slug, publish=args.publish)
