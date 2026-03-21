"""
Тесты приоритета персонажа: CharGen (char_per_slide) > rembg.
Запуск: python tests/test_chargen_compose.py
"""
import sys
import tempfile
from pathlib import Path

KARUSEL_ROOT = Path(__file__).resolve().parent.parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

from models.carousel_schema import Brand, CarouselData, SlideData
from agents.agent4_composer import compose_slides
from agents.agent3b_chargen import is_chargen_enabled


def _touch_png():
    fd, name = tempfile.mkstemp(suffix=".png")
    import os
    os.write(fd, b"\x89PNG\r\n\x1a\n")
    os.close(fd)
    return name


def test_compose_ai_over_rembg():
    ai1 = _touch_png()
    ai2 = _touch_png()
    try:
        slides = [
            SlideData(id=1, type="cover", use_character=True, photo_index=0),
            SlideData(id=2, type="benefits", use_character=True, photo_index=0),
        ]
        carousel = CarouselData(brand=Brand(name="Test"), slides=slides)
        composed = compose_slides(
            carousel,
            [Path(__file__)],
            character_png_by_photo_index={0: __file__},
            char_per_slide={1: ai1, 2: ai2},
            char_on_every_slide=False,
        )
        assert composed[0]["character_png"] == ai1
        assert composed[1]["character_png"] == ai2
        print("OK test_compose_ai_over_rembg")
    finally:
        import os
        for p in (ai1, ai2):
            try:
                os.unlink(p)
            except OSError:
                pass


def test_compose_fallback_rembg():
    rembg_p = _touch_png()
    try:
        slides = [
            SlideData(id=1, type="cover", use_character=True, photo_index=0),
        ]
        carousel = CarouselData(brand=Brand(name="Test"), slides=slides)
        composed = compose_slides(
            carousel,
            [Path(__file__)],
            character_png_by_photo_index={0: rembg_p},
            char_per_slide={},
            char_on_every_slide=False,
        )
        assert composed[0]["character_png"] == rembg_p
        print("OK test_compose_fallback_rembg")
    finally:
        import os
        try:
            os.unlink(rembg_p)
        except OSError:
            pass


def test_chargen_disabled_by_default():
    import os
    os.environ.pop("CHAR_VARIATION_ENABLED", None)
    assert is_chargen_enabled() is False
    print("OK test_chargen_disabled_by_default")


def main():
    test_compose_ai_over_rembg()
    test_compose_fallback_rembg()
    test_chargen_disabled_by_default()
    print("Все тесты chargen/compose пройдены.")


if __name__ == "__main__":
    main()
