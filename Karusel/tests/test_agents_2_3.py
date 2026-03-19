"""
Быстрый тест Agent 2 (Vision) и Agent 3 (Rembg).
Запуск:
  cd D:\\content-factory\\Karusel
  python tests/test_agents_2_3.py

Vision: ключи из config/.env или переменные окружения.
  OpenAI: OPENAI_API_KEY (+ опционально OPENAI_BASE_URL, OPENAI_MODEL)
  Локальный Ollama: VISION_BACKEND=ollama, OLLAMA_VISION_MODEL=llava (ollama pull llava)
"""
import asyncio
import os
import sys
from pathlib import Path

# Корень Karusel для импорта agents и models
KARUSEL_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = KARUSEL_ROOT.parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / "config" / ".env")
except Exception:
    pass

from agents.agent2_vision import VisionAgent
from agents.agent3_rembg import RembgAgent

# Пути к тестовым фото — замените на свои или создайте temp/test/
TEST_PHOTOS = [
    str(KARUSEL_ROOT / "temp" / "test" / "photo_0.jpg"),
    str(KARUSEL_ROOT / "temp" / "test" / "photo_1.jpg"),
]


async def main():
    # Проверяем что хотя бы один файл есть
    existing = [p for p in TEST_PHOTOS if Path(p).is_file()]
    if not existing:
        print("Нет тестовых фото. Положите JPG в Karusel/temp/test/ (photo_0.jpg, photo_1.jpg)")
        print("Или измените TEST_PHOTOS в этом файле.")
        return

    # ── Тест Vision ──────────────────────────────────────────────────
    print("=== AGENT 2: Vision ===")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip() or None
    vision_backend = os.environ.get("VISION_BACKEND", "").strip().lower()
    char_idx = None

    if vision_backend == "ollama":
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434").strip() or "http://localhost:11434"
        model = os.environ.get("OLLAMA_VISION_MODEL", "").strip() or "llava"
        print(f"  backend=ollama url={ollama_url} model={model}")
        vision = VisionAgent(backend="ollama", model=model, ollama_url=ollama_url)
        results = await vision.analyze(existing)
        for r in results:
            print(
                f"  Фото {r.index}: {r.recommended_role.value} "
                f"| quality={r.photo_quality.value} "
                f"| person={r.has_person}"
            )
        char_idx = VisionAgent.pick_best_character(results)
        print(f"  Лучший персонаж: фото #{char_idx}")
    elif api_key:
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or None
        model = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o"
        print(f"  backend=openai model={model}")
        vision = VisionAgent(
            backend="openai",
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        results = await vision.analyze(existing)
        for r in results:
            print(
                f"  Фото {r.index}: {r.recommended_role.value} "
                f"| quality={r.photo_quality.value} "
                f"| person={r.has_person}"
            )
        char_idx = VisionAgent.pick_best_character(results)
        print(f"  Лучший персонаж: фото #{char_idx}")
    else:
        print(
            "  Vision пропущен: задайте OPENAI_API_KEY или в config/.env:\n"
            "    VISION_BACKEND=ollama\n"
            "    OLLAMA_VISION_MODEL=llava\n"
            "  (ollama serve + ollama pull llava)"
        )

    # ── Тест Rembg ───────────────────────────────────────────────────
    print("\n=== AGENT 3: Rembg ===")
    if char_idx is not None and char_idx < len(existing):
        rembg = RembgAgent()
        try:
            out = await rembg.process(existing[char_idx])
            valid = RembgAgent.validate_output(out)
            print(f"  Результат: {out}")
            print(f"  Валиден:   {valid}")
        except Exception as e:
            print(f"  Ошибка: {e}")
    else:
        print("  Персонаж не найден или нет фото — rembg пропущен")


if __name__ == "__main__":
    asyncio.run(main())
