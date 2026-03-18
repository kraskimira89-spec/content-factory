# -*- coding: utf-8 -*-
"""
Проверка соединения с SD WebUI и Flask-прокси.

Запуск:
    python scripts/check_sd_connection.py           # полная проверка
    python scripts/check_sd_connection.py --quick   # только ping без тест-картинки
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "config" / ".env")

import requests  # noqa: E402

SD_URL      = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860").rstrip("/")
PROXY_URL   = os.getenv("IMAGE_GENERATOR_URL", "http://127.0.0.1:8000/generate")
TIMEOUT_SEC = 8

SEP  = "-" * 60
SEP2 = "=" * 60

TEST_PROMPT = (
    "1 woman, spa room, relaxed expression, soft warm lighting, "
    "white towels, photorealistic, highly detailed"
)
TEST_NEG = "lowres, blurry, bad anatomy, watermark, text, nudity"


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "[OK]" if ok else "[FAIL]"
    line   = f"  {status}  {label}"
    if detail:
        line += f"  —  {detail}"
    print(line)
    return ok


def ping_sd() -> tuple[bool, str]:
    """GET /sdapi/v1/options — самый быстрый индикатор."""
    try:
        r = requests.get(f"{SD_URL}/sdapi/v1/options", timeout=TIMEOUT_SEC)
        if r.status_code == 200:
            model = r.json().get("sd_model_checkpoint", "?")
            return True, f"модель: {model}"
        return False, f"HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "нет соединения (SD не запущен или порт неверный)"
    except requests.exceptions.Timeout:
        return False, f"таймаут {TIMEOUT_SEC}s"
    except Exception as e:
        return False, str(e)


def ping_proxy() -> tuple[bool, str]:
    """GET /health на Flask-прокси."""
    health_url = PROXY_URL.replace("/generate", "/health")
    try:
        r = requests.get(health_url, timeout=TIMEOUT_SEC)
        if r.status_code in (200, 503):
            data = r.json()
            sd_ok = data.get("sd_webui", False)
            return True, f"sd_webui={sd_ok}"
        return False, f"HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Flask API не запущен (нужно: python scripts/image_generate_api.py)"
    except Exception as e:
        return False, str(e)


def test_generate() -> tuple[bool, str]:
    """POST /generate с тестовым промптом — проверяет весь пайплайн."""
    try:
        r = requests.post(
            PROXY_URL,
            json={
                "prompt":          TEST_PROMPT,
                "negative_prompt": TEST_NEG,
                "width":  512,
                "height": 512,
                "steps":  10,    # мало шагов — быстрая проверка
                "cfg_scale": 7,
                "sampler_name": "DPM++ 2M Karras",
            },
            timeout=300,
        )
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            out_path = PROJECT_ROOT / "output" / "images" / "_connection_test.png"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(r.content)
            return True, f"PNG сохранён: {out_path}"
        if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""):
            data = r.json()
            if "error" in data:
                return False, data["error"]
        return False, f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return False, "таймаут 120s — SD перегружен или не отвечает"
    except Exception as e:
        return False, str(e)


def show_config() -> None:
    print(f"\n  SD WebUI URL:   {SD_URL}")
    print(f"  Flask proxy:    {PROXY_URL}")
    print(f"  SD root (.env): {os.getenv('SD_WEBUI_ROOT', 'не задан')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверка соединения с SD WebUI")
    parser.add_argument("--quick", action="store_true", help="Только ping, без тест-картинки")
    args = parser.parse_args()

    print(f"\n{SEP2}")
    print("  CHECK SD CONNECTION")
    print(SEP2)
    show_config()
    print(f"\n{SEP}")

    sd_ok,    sd_info    = ping_sd()
    proxy_ok, proxy_info = ping_proxy()

    check("SD WebUI доступен",   sd_ok,    sd_info)
    check("Flask API доступен",  proxy_ok, proxy_info)

    if not args.quick:
        print(f"{SEP}")
        print("  Тестовая генерация (10 шагов)... может занять 20–60 с")
        gen_ok, gen_info = test_generate()
        check("Генерация картинки",  gen_ok, gen_info)

    print(f"{SEP}")

    all_ok = sd_ok and proxy_ok and (args.quick or gen_ok)
    if all_ok:
        print("  Всё работает. Пайплайн готов к запуску.")
    else:
        print("  Есть проблемы — см. [FAIL] выше.")
        if not sd_ok:
            print(f"\n  Как запустить SD:")
            root = os.getenv("SD_WEBUI_ROOT", "D:/AI/stable-diffusion-webui")
            print(f"    1. Открой {root}\\webui-user.bat")
            print(f"    2. Убедись что в нём есть: set COMMANDLINE_ARGS=--api")
            print(f"    3. Запусти webui-user.bat и дождись сообщения 'Running on http://127.0.0.1:786x'")
        if not proxy_ok:
            print(f"\n  Как запустить Flask API:")
            print(f"    python scripts/image_generate_api.py")
    print(f"{SEP2}\n")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
