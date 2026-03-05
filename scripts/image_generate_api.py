"""
API-сервер /generate для agent9.
Прокси к Stable Diffusion WebUI (sdapi/v1/txt2img) или ComfyUI.

Запуск: python scripts/image_generate_api.py
Слушает http://127.0.0.1:8000/generate

Переменные окружения (config/.env):
  SD_WEBUI_URL — URL Stable Diffusion WebUI (по умолчанию http://127.0.0.1:7860)
  IMAGE_API_PORT — порт этого сервера (по умолчанию 8000)
"""
import base64
import os
import sys
from pathlib import Path

# Кодировка вывода в консоль (русский в .env и сообщения об ошибках)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "config" / ".env")

SD_WEBUI_URL = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860").rstrip("/")
PORT = int(os.getenv("IMAGE_API_PORT", "8000"))


def generate_image(prompt: str, width: int, height: int) -> bytes:
    """Вызов SD WebUI txt2img, возвращает сырые байты PNG."""
    import requests
    payload = {
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, distorted, text, watermark, logo",
        "width": min(max(width, 512), 1536),
        "height": min(max(height, 512), 1536),
        "steps": 25,
        "sampler_name": "DPM++ 2M Karras",
        "cfg_scale": 7,
        "seed": -1,
    }
    resp = requests.post(
        f"{SD_WEBUI_URL}/sdapi/v1/txt2img",
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("images"):
        raise ValueError("SD WebUI вернул пустой ответ")
    return base64.b64decode(data["images"][0])


def main():
    try:
        from flask import Flask, request, Response
    except ImportError:
        print("Установите Flask: pip install flask")
        sys.exit(1)
    import requests

    app = Flask(__name__)

    @app.route("/generate", methods=["POST"])
    def handle_generate():
        try:
            data = request.get_json() or {}
            prompt = data.get("prompt", "")
            width = int(data.get("width", 1280))
            height = int(data.get("height", 720))
            if not prompt:
                return {"error": "prompt required"}, 400
            img_bytes = generate_image(prompt, width, height)
            return Response(img_bytes, mimetype="image/png")
        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/health")
    def health():
        try:
            r = requests.get(f"{SD_WEBUI_URL}/sdapi/v1/options", timeout=5)
            sd_ok = r.status_code == 200
        except Exception:
            sd_ok = False
        return {"ok": True, "sd_webui": sd_ok}, 200 if sd_ok else 503

    print(f"Image API: http://127.0.0.1:{PORT}/generate")
    print(f"Backend:   {SD_WEBUI_URL} (SD WebUI)")
    print("Остановка: Ctrl+C")
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
