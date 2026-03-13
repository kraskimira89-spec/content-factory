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


DEFAULT_NEGATIVE = "lowres, blurry, bad anatomy, bad proportions, deformed, watermark, text, logo, nudity"


def generate_image(
    prompt: str,
    width: int = 832,
    height: int = 512,
    negative_prompt: str = "",
    steps: int = 28,
    cfg_scale: float = 7.0,
    sampler_name: str = "DPM++ 2M Karras",
    seed: int = -1,
) -> bytes:
    """Вызов SD WebUI txt2img, возвращает сырые байты PNG."""
    import requests
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
        "width": min(max(width, 512), 1536),
        "height": min(max(height, 512), 1536),
        "steps": steps,
        "sampler_name": sampler_name,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "batch_size": 1,
        "n_iter": 1,
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
            if not prompt:
                return {"error": "prompt required"}, 400
            img_bytes = generate_image(
                prompt=prompt,
                width=int(data.get("width", 832)),
                height=int(data.get("height", 512)),
                negative_prompt=data.get("negative_prompt", ""),
                steps=int(data.get("steps", 28)),
                cfg_scale=float(data.get("cfg_scale", 7.0)),
                sampler_name=data.get("sampler_name", "DPM++ 2M Karras"),
                seed=int(data.get("seed", -1)),
            )
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
