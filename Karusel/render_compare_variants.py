"""
Пакетный рендер карусели в нескольких дизайн-вариантах.

Использование:
  python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt
  python Karusel/render_compare_variants.py --photos img1.jpg img2.jpg --brief "ТЗ текст" --output-root Karusel/compare_out_py
  python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt
  python Karusel/render_compare_variants.py --photos-dir Karusel/demo_photos --brief-file Karusel/demo_brief.txt --variants premium,premium_alt --open-report
"""
from __future__ import annotations

import argparse
import html
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

KARUSEL_ROOT = Path(__file__).resolve().parent
if str(KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KARUSEL_ROOT))

from agents.orchestrator import run_pipeline


@dataclass
class VariantSpec:
    name: str
    design_tokens: Path | None = None
    figma_map: Path | None = None


PREVIEW_SLIDES_MAX = 3  # мини-лента: первые 2–3 слайда

@dataclass
class RenderResult:
    name: str
    status: str
    slides_count: int
    elapsed_sec: float
    output_dir: Path
    error: str = ""
    preview_paths: list[Path] = field(default_factory=list)  # первые 2–3 слайда для мини-ленты


DEFAULT_VARIANTS = [
    VariantSpec(name="default"),
    VariantSpec(name="ocean", design_tokens=KARUSEL_ROOT / "config" / "demo_brand_tokens_ocean_med.json"),
    VariantSpec(
        name="ocean_alt",
        design_tokens=KARUSEL_ROOT / "config" / "demo_brand_tokens_ocean_med.json",
        figma_map=KARUSEL_ROOT / "config" / "demo_figma_template_map_alt.json",
    ),
    VariantSpec(name="premium", design_tokens=KARUSEL_ROOT / "config" / "demo_brand_tokens_premium_gold.json"),
    VariantSpec(
        name="premium_alt",
        design_tokens=KARUSEL_ROOT / "config" / "demo_brand_tokens_premium_gold.json",
        figma_map=KARUSEL_ROOT / "config" / "demo_figma_template_map_alt.json",
    ),
]

VARIANTS_BY_NAME = {item.name: item for item in DEFAULT_VARIANTS}


def _resolve_photos(args) -> list[Path]:
    photo_paths: list[Path] = []
    if args.photos:
        photo_paths = [Path(p) for p in args.photos]
    elif args.photos_dir and args.photos_dir.is_dir():
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            photo_paths.extend(args.photos_dir.glob(ext))
        photo_paths = sorted(photo_paths)
    if not photo_paths:
        raise ValueError("Укажите фото: --photos file1.jpg file2.jpg или --photos-dir ./dir")
    return photo_paths


def _resolve_brief(args) -> str:
    if args.brief:
        return args.brief.strip()
    if args.brief_file and args.brief_file.is_file():
        return args.brief_file.read_text(encoding="utf-8").strip()
    raise ValueError("Укажите ТЗ: --brief '...' или --brief-file tz.txt")


def _resolve_variants(raw: str | None) -> list[VariantSpec]:
    """Возвращает список вариантов по CSV-строке или все по умолчанию."""
    if not raw:
        return DEFAULT_VARIANTS
    names = [item.strip() for item in raw.split(",") if item.strip()]
    if not names:
        raise ValueError("Параметр --variants пуст. Пример: --variants premium,premium_alt")
    unknown = [name for name in names if name not in VARIANTS_BY_NAME]
    if unknown:
        available = ", ".join(VARIANTS_BY_NAME.keys())
        raise ValueError(
            f"Неизвестные варианты: {', '.join(unknown)}. Доступно: {available}"
        )
    return [VARIANTS_BY_NAME[name] for name in names]


def _render_variant(
    variant: VariantSpec,
    photo_paths: list[Path],
    brief_text: str,
    output_root: Path,
) -> RenderResult:
    out_dir = output_root / variant.name
    started = time.perf_counter()
    try:
        slide_paths = run_pipeline(
            photo_paths,
            brief_text,
            out_dir,
            run_vision=False,
            run_poster=False,
            design_tokens_path=variant.design_tokens,
            figma_map_path=variant.figma_map,
        )
        elapsed = time.perf_counter() - started
        preview_paths = [Path(p) for p in slide_paths[:PREVIEW_SLIDES_MAX]] if slide_paths else []
        return RenderResult(
            name=variant.name,
            status="OK",
            slides_count=len(slide_paths),
            elapsed_sec=elapsed,
            output_dir=out_dir,
            preview_paths=preview_paths,
        )
    except Exception as e:
        elapsed = time.perf_counter() - started
        return RenderResult(
            name=variant.name,
            status="ERROR",
            slides_count=0,
            elapsed_sec=elapsed,
            output_dir=out_dir,
            error=str(e),
            preview_paths=[],
        )


def _print_summary(results: list[RenderResult]) -> None:
    print("\n=== Summary ===")
    print(f"{'Variant':<14} {'Status':<8} {'Slides':<8} {'Time(s)':<10} Output")
    print("-" * 78)
    for item in results:
        print(
            f"{item.name:<14} {item.status:<8} {item.slides_count:<8} "
            f"{item.elapsed_sec:<10.2f} {item.output_dir}"
        )
        if item.error:
            print(f"{'':<14} {'':<8} {'':<8} {'':<10} error: {item.error}")


def _generate_index_html(
    results: list[RenderResult],
    output_root: Path,
    brief_text: str,
    selected_variants: list[VariantSpec],
) -> Path:
    """Генерирует простой index.html со ссылками на папки результатов."""
    index_path = output_root / "index.html"
    escaped_brief = html.escape(brief_text[:600])
    variants_text = ", ".join(item.name for item in selected_variants)
    rows = []
    for item in results:
        rel_dir = item.output_dir.name
        status_class = "ok" if item.status == "OK" else "error"
        error_html = f"<div class=\"error-text\">{html.escape(item.error)}</div>" if item.error else ""
        preview_parts = []
        for p in (item.preview_paths or [])[:PREVIEW_SLIDES_MAX]:
            if p and p.is_file():
                try:
                    preview_rel = p.relative_to(output_root).as_posix()
                except ValueError:
                    continue
                preview_parts.append(
                    f'<a href="{html.escape(preview_rel)}" target="_blank">'
                    f'<img class="preview-img" src="{html.escape(preview_rel)}" alt="{html.escape(item.name)}"></a>'
                )
        preview_html = f'<div class="preview-strip">{"".join(preview_parts)}</div>' if preview_parts else ""
        rows.append(
            f"""
            <tr>
              <td><a href="{html.escape(rel_dir)}/">{html.escape(item.name)}</a></td>
              <td class="{status_class}">{html.escape(item.status)}</td>
              <td>{item.slides_count}</td>
              <td>{item.elapsed_sec:.2f}</td>
              <td>{preview_html}</td>
              <td><a href="{html.escape(rel_dir)}/">{html.escape(str(item.output_dir))}</a>{error_html}</td>
            </tr>
            """
        )
    html_text = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Karusel Compare Summary</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      background: #f7f7f7;
      color: #222;
    }}
    h1, h2 {{
      margin: 0 0 12px;
    }}
    .meta, .brief {{
      background: #fff;
      border-radius: 12px;
      padding: 16px 18px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
      margin-bottom: 16px;
    }}
    .brief {{
      white-space: pre-wrap;
      line-height: 1.5;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid #eee;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #fafafa;
    }}
    .ok {{
      color: #0a7a2f;
      font-weight: 700;
    }}
    .error {{
      color: #b42318;
      font-weight: 700;
    }}
    .error-text {{
      margin-top: 6px;
      color: #b42318;
      font-size: 13px;
    }}
    .preview-strip {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .preview-img {{
      width: 100px;
      height: auto;
      max-height: 130px;
      object-fit: cover;
      border-radius: 8px;
      border: 1px solid #ddd;
      background: #fff;
    }}
    a {{
      color: #0b63ce;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    code {{
      background: #f1f1f1;
      padding: 2px 6px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <h1>Karusel Compare Summary</h1>
  <div class="meta">
    <div><strong>Варианты:</strong> <code>{html.escape(variants_text)}</code></div>
    <div><strong>Папка результатов:</strong> <code>{html.escape(str(output_root))}</code></div>
  </div>
  <div class="brief">
    <strong>ТЗ:</strong><br>
    {escaped_brief}
  </div>
  <table>
    <thead>
      <tr>
        <th>Variant</th>
        <th>Status</th>
        <th>Slides</th>
        <th>Time(s)</th>
        <th>Preview</th>
        <th>Output</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    index_path.write_text(html_text, encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Karusel: пакетный рендер нескольких дизайн-вариантов с summary"
    )
    parser.add_argument("--photos", nargs="*", help="Пути к фото")
    parser.add_argument("--photos-dir", type=Path, help="Папка с фото (все .jpg .png)")
    parser.add_argument("--brief", type=str, help="Текст ТЗ")
    parser.add_argument("--brief-file", type=Path, help="Файл с текстом ТЗ")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("Karusel/compare_out_py"),
        help="Корневая папка для наборов default/ocean/ocean_alt/premium/premium_alt",
    )
    parser.add_argument(
        "--variants",
        type=str,
        help="CSV-список вариантов. Пример: premium,premium_alt",
    )
    parser.add_argument(
        "--open-report",
        action="store_true",
        help="После рендера открыть index.html в браузере",
    )
    args = parser.parse_args()

    try:
        photo_paths = _resolve_photos(args)
        brief_text = _resolve_brief(args)
        selected_variants = _resolve_variants(args.variants)
    except ValueError as e:
        print(e)
        return 1

    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    results: list[RenderResult] = []
    total = len(selected_variants)
    for idx, variant in enumerate(selected_variants, start=1):
        print(f"\n[{idx}/{total}] Render {variant.name}...")
        result = _render_variant(variant, photo_paths, brief_text, output_root)
        results.append(result)

    _print_summary(results)
    index_path = _generate_index_html(results, output_root, brief_text, selected_variants)
    print(f"\nHTML summary: {index_path}")
    if args.open_report:
        try:
            webbrowser.open(index_path.resolve().as_uri())
            print("Report opened in browser.")
        except Exception as e:
            print(f"Не удалось открыть отчёт автоматически: {e}")
    return 1 if any(item.status != "OK" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
