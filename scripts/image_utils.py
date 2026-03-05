# scripts/image_utils.py — сохранение сгенерированных изображений (PNG→JPEG для .jpg)
"""
При сохранении в .jpg файл с PNG-данными от SD WebUI конвертируем в JPEG,
чтобы просмотрщики и браузеры не показывали артефакты или серые квадраты.
"""
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def save_image_bytes(data: bytes, path: Path, *, jpeg_quality: int = 95) -> None:
    """
    Сохраняет байты изображения в path.
    Если path заканчивается на .jpg/.jpeg, а data — PNG, конвертирует в JPEG.
    Пустые данные не записываются (защита от битых/пустых файлов).
    """
    if not data:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg") and len(data) >= 8 and data[:8] == PNG_SIGNATURE:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(path, "JPEG", quality=jpeg_quality)
            return
        except Exception:
            pass
    path.write_bytes(data)
