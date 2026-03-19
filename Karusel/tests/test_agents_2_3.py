"""
Быстрый тест Agent 2 (Vision) и Agent 3 (Rembg).
Запуск из корня content-factory:
  cd Karusel && python -m tests.test_agents_2_3
Или из Karusel с OPENAI_API_KEY:
  set OPENAI_API_KEY=sk-...
  python tests/test_agents_2_3.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Корень Karusel для импорта agents и models
KARUSEL_ROOT = Path(__file__).resolve().parent.parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

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
    char_idx = None
    if not api_key:
        print("  OPENAI_API_KEY не задан — пропуск Vision (или используйте backend=ollama)")
    else:
        vision = VisionAgent(
            backend="openai",
            model="gpt-4o",
            api_key=api_key,
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
