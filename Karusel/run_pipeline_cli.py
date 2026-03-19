"""
CLI пайплайна карусели без бота.
Использование:
  python run_pipeline_cli.py --photos img1.jpg img2.jpg --brief "ТЗ текст" --output out_dir
  python run_pipeline_cli.py --photos-dir ./photos --brief-file tz.txt --output out_dir
  python run_pipeline_cli.py --photos-dir ./photos --brief-file tz.txt --design-tokens Karusel/config/demo_brand_tokens_ocean_med.json --output out_dir
  python run_pipeline_cli.py --photos-dir ./photos --brief-file tz.txt --design-tokens Karusel/config/demo_brand_tokens_premium_gold.json --figma-map Karusel/config/figma_template_map.json --output out_dir
"""
import argparse
import sys
from pathlib import Path

KARUSEL_ROOT = Path(__file__).resolve().parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

from agents.orchestrator import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Karusel: генерация слайдов карусели по фото и ТЗ")
    parser.add_argument("--photos", nargs="*", help="Пути к фото")
    parser.add_argument("--photos-dir", type=Path, help="Папка с фото (все .jpg .png)")
    parser.add_argument("--brief", type=str, help="Текст ТЗ")
    parser.add_argument("--brief-file", type=Path, help="Файл с текстом ТЗ")
    parser.add_argument("--output", "-o", type=Path, default=Path("output"), help="Папка для слайдов")
    parser.add_argument("--design-tokens", type=Path, help="Альтернативный JSON дизайн-токенов для проверки другого бренда")
    parser.add_argument("--figma-map", type=Path, help="Альтернативный JSON карты Figma frame -> template/layout")
    args = parser.parse_args()

    photo_paths = []
    if args.photos:
        photo_paths = [Path(p) for p in args.photos]
    elif args.photos_dir and args.photos_dir.is_dir():
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            photo_paths.extend(args.photos_dir.glob(ext))
        photo_paths = sorted(photo_paths)
    if not photo_paths:
        print("Укажите фото: --photos file1.jpg file2.jpg или --photos-dir ./dir")
        sys.exit(1)

    brief_text = ""
    if args.brief:
        brief_text = args.brief
    elif args.brief_file and args.brief_file.is_file():
        brief_text = args.brief_file.read_text(encoding="utf-8")
    if not brief_text.strip():
        print("Укажите ТЗ: --brief '...' или --brief-file tz.txt")
        sys.exit(1)

    output_dir = args.output
    paths = run_pipeline(
        photo_paths,
        brief_text,
        output_dir,
        run_vision=False,
        run_poster=False,
        design_tokens_path=args.design_tokens,
        figma_map_path=args.figma_map,
    )
    print("Готово. Слайды:", paths)


if __name__ == "__main__":
    main()
