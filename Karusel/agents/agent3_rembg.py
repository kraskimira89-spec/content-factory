"""
Agent 3 — Rembg: вырезка персонажа из фото → PNG с прозрачным фоном.
Класс RembgAgent (async) + обёртка process_photo_for_character для orchestrator.
"""
from __future__ import annotations

import asyncio
import io
import shutil
import sys
from pathlib import Path

from PIL import Image

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger

logger = get_logger("agent3_rembg")

# ── Константы ─────────────────────────────────────────────────────────────────

REMBG_MODEL = "u2net_human_seg"
TARGET_CHAR_HEIGHT = 1000
MIN_VALID_SIZE_BYTES = 10_000

# Совместимость с preset: дефолтный character box (orchestrator передаёт character_box)
DEFAULT_CHARACTER_BOX = (540, 1350)


# ── Основной класс ────────────────────────────────────────────────────────────

class RembgAgent:
    """
    Вырезает фон из фото персонажа.
    Результат: char_ready.png в той же папке что исходник (или в output_dir при вызове через обёртку).
    """

    def __init__(self):
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                from rembg import new_session
                self._session = new_session(REMBG_MODEL)
                logger.info("rembg сессия инициализирована: %s", REMBG_MODEL)
            except Exception as e:
                logger.error("rembg инициализация: %s", e)
                raise
        return self._session

    async def process(self, photo_path: str) -> str:
        """
        Вырезает фон из фото. Возвращает путь к char_ready.png.
        Сохраняет в папку исходного файла.
        """
        path = Path(photo_path)
        if not path.exists():
            raise FileNotFoundError(f"Фото не найдено: {photo_path}")
        output_path = path.parent / "char_ready.png"
        logger.info("Rembg: начало обработки %s", path.name)
        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(
            None,
            self._process_sync,
            photo_path,
            str(output_path),
        )
        logger.info("Rembg: готово → %s", output_path.name)
        return result_path

    def _process_sync(self, input_path: str, output_path: str) -> str:
        from rembg import remove

        session = self._get_session()
        with open(input_path, "rb") as f:
            raw_bytes = f.read()

        img_original = Image.open(input_path).convert("RGB")
        img_prepared, scale_factor = self._prepare_input(img_original)
        if scale_factor < 1.0:
            buf = io.BytesIO()
            img_prepared.save(buf, format="JPEG", quality=95)
            raw_bytes = buf.getvalue()

        result_bytes = remove(
            raw_bytes,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )

        result_img = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        result_img = self._autocrop(result_img)
        result_img = self._scale_to_slide(result_img)
        result_img = self._clean_alpha(result_img)
        result_img.save(output_path, "PNG", optimize=True)

        size = Path(output_path).stat().st_size
        if size < MIN_VALID_SIZE_BYTES:
            raise ValueError(
                f"char_ready.png подозрительно мал ({size} байт). Возможно rembg не нашёл персонажа."
            )
        logger.info("char_ready.png: %s×%s px, %s KB", result_img.size[0], result_img.size[1], size // 1024)
        return output_path

    @staticmethod
    def _prepare_input(img: Image.Image, max_side: int = 1500) -> tuple[Image.Image, float]:
        w, h = img.size
        longest = max(w, h)
        if longest <= max_side:
            return img, 1.0
        scale = max_side / longest
        new_w, new_h = int(w * scale), int(h * scale)
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS), scale

    @staticmethod
    def _autocrop(img: Image.Image) -> Image.Image:
        bbox = img.getbbox()
        if bbox is None:
            logger.warning("_autocrop: bbox пустой")
            return img
        pad = 10
        left = max(0, bbox[0] - pad)
        top = max(0, bbox[1] - pad)
        right = min(img.width, bbox[2] + pad)
        bottom = min(img.height, bbox[3] + pad)
        return img.crop((left, top, right, bottom))

    @staticmethod
    def _scale_to_slide(img: Image.Image, target_height: int = TARGET_CHAR_HEIGHT) -> Image.Image:
        w, h = img.size
        if h == target_height:
            return img
        scale = target_height / h
        new_w = int(w * scale)
        return img.resize((new_w, target_height), Image.Resampling.LANCZOS)

    @staticmethod
    def _clean_alpha(img: Image.Image, threshold: int = 30) -> Image.Image:
        import numpy as np
        data = np.array(img)
        alpha = data[:, :, 3]
        data[alpha < threshold, 3] = 0
        data[alpha > (255 - threshold), 3] = 255
        return Image.fromarray(data, "RGBA")

    async def process_many(self, photo_paths: list[str]) -> list[str | None]:
        """Обрабатывает несколько фото последовательно. None если не удалось."""
        results: list[str | None] = []
        for path in photo_paths:
            try:
                out = await self.process(path)
                results.append(out)
            except Exception as e:
                logger.warning("process_many: пропускаем %s: %s", path, e)
                results.append(None)
        return results

    @staticmethod
    def validate_output(png_path: str) -> bool:
        """Проверяет что char_ready.png существует, не пустой и с альфой."""
        p = Path(png_path)
        if not p.exists() or p.stat().st_size < MIN_VALID_SIZE_BYTES:
            return False
        try:
            img = Image.open(png_path)
            if img.mode != "RGBA":
                return False
            import numpy as np
            alpha = np.array(img)[:, :, 3]
            return bool((alpha > 128).sum() > 1000)
        except Exception:
            return False


# ── Совместимость с orchestrator: синхронная обёртка ───────────────────────────

def process_photo_for_character(
    image_path: str | Path,
    output_dir: str | Path | None = None,
    do_crop: bool = True,
    character_box: dict | None = None,
) -> str:
    """
    Синхронная обёртка для orchestrator: вырезка фона + сохранение в output_dir.
    Возвращает путь к PNG (например output_dir/{stem}_char.png).
    character_box из preset не меняет логику RembgAgent (масштаб по TARGET_CHAR_HEIGHT).
    """
    path = Path(image_path)
    if output_dir is None:
        output_dir = path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Работаем во временном файле в output_dir, чтобы char_ready.png оказался там
    work_path = output_dir / path.name
    if path.resolve() != work_path.resolve():
        shutil.copy2(path, work_path)
    else:
        work_path = path

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    agent = RembgAgent()
    result_path = loop.run_until_complete(agent.process(str(work_path)))
    # result_path = work_path.parent / "char_ready.png"
    out_final = output_dir / f"{path.stem}_char.png"
    if Path(result_path).resolve() != out_final.resolve():
        shutil.copy2(result_path, out_final)
    return str(out_final)


def smart_crop_character(
    png_path: str | Path,
    target_size: tuple[int, int] | None = None,
    character_box: dict | None = None,
    output_suffix: str = "_char",
) -> str:
    """Кроп по bbox альфа-канала. Оставлено для совместимости; основной поток через RembgAgent."""
    from PIL import Image
    png_path = Path(png_path)
    if target_size is None and character_box:
        target_size = (
            int(character_box.get("width", DEFAULT_CHARACTER_BOX[0])),
            int(character_box.get("height", DEFAULT_CHARACTER_BOX[1])),
        )
    if target_size is None:
        target_size = DEFAULT_CHARACTER_BOX
    out_path = png_path.parent / f"{png_path.stem}{output_suffix}.png"
    img = Image.open(png_path).convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        img.save(out_path, "PNG")
        return str(out_path)
    cropped = img.crop(bbox)
    cropped.thumbnail(target_size, Image.Resampling.LANCZOS)
    cropped.save(out_path, "PNG")
    return str(out_path)


def remove_background(
    image_path: str | Path,
    output_path: str | Path | None = None,
    session_name: str = "u2net_human_seg",
    alpha_matting: bool = True,
) -> str:
    """Только удаление фона без кропа. Для совместимости со старыми вызовами."""
    import rembg
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path}")
    out = output_path or path.parent / f"{path.stem}_nobg.png"
    out = Path(out)
    with open(path, "rb") as f:
        raw = f.read()
    session = rembg.new_session(session_name)
    result = rembg.remove(raw, session=session, alpha_matting=alpha_matting)
    img = Image.open(io.BytesIO(result))
    img.save(out, "PNG")
    return str(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python agent3_rembg.py <path_to_photo> [output_dir]")
        sys.exit(1)
    photo = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = process_photo_for_character(photo, output_dir=out_dir)
    print("Результат:", result)
