"""
Agent 3 — Rembg: вырезка персонажа из фото → PNG с прозрачным фоном.
Использует rembg с сессией u2net_human_seg и alpha_matting для мягких краёв.
"""
import io
import sys
from pathlib import Path

from PIL import Image

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger
logger = get_logger("agent3_rembg")


def remove_background(
    image_path: str | Path,
    output_path: str | Path | None = None,
    session_name: str = "u2net_human_seg",
    alpha_matting: bool = True,
) -> str:
    """
    Удаляет фон с изображения. Возвращает путь к сохранённому PNG.
    """
    import rembg
    from rembg.sessions import sessions_names

    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {image_path}")

    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_nobg.png"
    else:
        output_path = Path(output_path)

    with open(image_path, "rb") as f:
        input_data = f.read()

    session = rembg.new_session(session_name)
    result = rembg.remove(
        input_data,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
    )

    img = Image.open(io.BytesIO(result))
    img.save(output_path, "PNG")
    logger.info("Фон удалён: %s -> %s", image_path.name, output_path.name)
    return str(output_path)


DEFAULT_CHARACTER_BOX = (540, 1350)  # портретный слот по умолчанию

def smart_crop_character(
    png_path: str | Path,
    target_size: tuple[int, int] | None = None,
    character_box: dict | None = None,
    output_suffix: str = "_char",
) -> str:
    """
    Кропает PNG с персонажем по bbox альфа-канала, подгоняет под target_size.
    target_size задаётся явно или через character_box из preset (width, height).
    Возвращает путь к сохранённому PNG.
    """
    if target_size is None and character_box:
        target_size = (
            int(character_box.get("width", DEFAULT_CHARACTER_BOX[0])),
            int(character_box.get("height", DEFAULT_CHARACTER_BOX[1])),
        )
    if target_size is None:
        target_size = DEFAULT_CHARACTER_BOX
    png_path = Path(png_path)
    out_path = png_path.parent / f"{png_path.stem}{output_suffix}.png"
    if out_path == png_path:
        out_path = png_path.parent / f"{png_path.stem}_cropped.png"

    img = Image.open(png_path).convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        # Нет альфа или пусто — сохраняем как есть с thumbnail
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        img.save(out_path, "PNG")
        return str(out_path)

    cropped = img.crop(bbox)
    cropped.thumbnail(target_size, Image.Resampling.LANCZOS)
    cropped.save(out_path, "PNG")
    logger.info("Кроп персонажа: %s -> %s", png_path.name, out_path.name)
    return str(out_path)


def process_photo_for_character(
    image_path: str | Path,
    output_dir: str | Path | None = None,
    do_crop: bool = True,
    character_box: dict | None = None,
) -> str:
    """
    Полный цикл: удаление фона + опционально кроп.
    character_box из render preset (width, height) — целевой размер кропа; иначе 540×1350.
    Возвращает путь к финальному PNG (nobg или char).
    """
    image_path = Path(image_path)
    if output_dir is None:
        output_dir = image_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / f"{image_path.stem}_nobg.png"
    nobg = remove_background(image_path, output_path=png_path)
    if do_crop:
        return smart_crop_character(nobg, character_box=character_box)
    return nobg


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python agent3_rembg.py <path_to_photo> [output_dir]")
        sys.exit(1)
    path = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = process_photo_for_character(path, output_dir=out_dir)
    print("Результат:", result)
