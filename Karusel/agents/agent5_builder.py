"""
Agent 5 — Builder: Jinja2-шаблоны + Playwright → JPG слайды 1080×1350.
Сборка слайдов параллельно в одном браузере.
"""
import asyncio
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

try:
    from playwright.async_api import async_playwright
except ImportError as e:
    raise ImportError(
        "Karusel Agent 5: нужен Microsoft Playwright и Chromium.\n"
        "  pip install playwright\n"
        "  playwright install chromium\n"
        "См. Karusel/docs/pipeline-run-steps.md (частые ошибки)."
    ) from e

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
_TEMPLATES_DIR = _KARUSEL_ROOT / "templates" / "carousel"
_CONFIG_TOKENS_PATH = _KARUSEL_ROOT / "config" / "brand_colors.json"
_FIGMA_TEMPLATE_MAP_PATH = _KARUSEL_ROOT / "config" / "figma_template_map.json"
_PRESETS_DIR = _KARUSEL_ROOT / "config" / "presets"
_EXPORT_PROFILES_PATH = _KARUSEL_ROOT / "config" / "export_profiles.json"
_ASSETS_TOKENS_PATH = _KARUSEL_ROOT / "assets" / "carousel" / "brand" / "colors.json"
_DEFAULT_LOGO_PATH = _KARUSEL_ROOT / "assets" / "carousel" / "brand" / "logo.png"

# Маппинг type слайда → имя файла шаблона / frame в Figma
TEMPLATE_MAP = {
    "cover": {"template": "cover.html", "frame_name": "Cover"},
    "benefits": {"template": "benefits.html", "frame_name": "Benefits"},
    "indications": {"template": "indications.html", "frame_name": "Indications"},
    "howworks": {"template": "howworks.html", "frame_name": "HowWorks"},
    "target": {"template": "target_audience.html", "frame_name": "TargetAudience"},
    "results": {"template": "results.html", "frame_name": "Results"},
    "photo_raw": {"template": "photo_raw.html", "frame_name": "PhotoRaw"},
    "cta": {"template": "cta.html", "frame_name": "CTA"},
}

VIEWPORT = {"width": 1080, "height": 1350}
JPEG_QUALITY = 92

if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))
from logger import get_logger
logger = get_logger("agent5_builder")


def _deep_merge(base: dict, override: dict) -> dict:
    """Рекурсивное слияние: override поверх base. Вложенные dict объединяются, остальное перезаписывается."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_design_tokens(design_tokens_path: str | Path | None = None) -> dict:
    """Загружает дизайн-токены из config, brand assets и опционального файла бренда (deep merge)."""
    tokens: dict = {}
    paths = [_ASSETS_TOKENS_PATH, _CONFIG_TOKENS_PATH]
    if design_tokens_path:
        paths.append(Path(design_tokens_path))
    for path in paths:
        if not path.is_file():
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                tokens = _deep_merge(tokens, loaded)
        except json.JSONDecodeError as e:
            logger.warning("Не удалось прочитать токены %s: %s", path, e)
    return tokens


def _resolve_export_profile(profile_id: str) -> str | None:
    """По id экспорт-профиля (telegram_album, instagram_feed_square, …) возвращает имя preset или None."""
    if not profile_id or "/" in profile_id or "\\" in profile_id:
        return None
    if not _EXPORT_PROFILES_PATH.is_file():
        return None
    try:
        profiles = json.loads(_EXPORT_PROFILES_PATH.read_text(encoding="utf-8"))
        entry = profiles.get(profile_id) if isinstance(profiles, dict) else None
        if isinstance(entry, dict) and entry.get("preset"):
            return entry["preset"]
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _load_preset(preset_path: str | Path | None = None) -> dict:
    """Загружает render preset. preset_path — путь к JSON, имя preset или id export profile (telegram_album, …)."""
    if not preset_path:
        return {}
    raw = str(preset_path).strip()
    # Разрешение export profile → preset name
    if raw and "/" not in raw and "\\" not in raw:
        resolved = _resolve_export_profile(raw)
        if resolved:
            raw = resolved
    path = Path(raw)
    if not path.is_file() and _PRESETS_DIR.is_dir():
        by_name = _PRESETS_DIR / f"{path.stem or path.name}.json"
        if by_name.is_file():
            path = by_name
    if not path.is_file():
        logger.warning("Preset не найден: %s", preset_path)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as e:
        logger.warning("Не удалось прочитать preset %s: %s", path, e)
        return {}


def _preset_to_tokens(preset: dict) -> dict:
    """Преобразует preset (viewport, safe_area, content, character_box) в структуру токенов для layout/CSS."""
    if not preset:
        return {}
    out = {}
    vp = preset.get("viewport") or {}
    if vp:
        out.setdefault("frame_size", {})["width"] = vp.get("width")
        out["frame_size"]["height"] = vp.get("height")
    sa = preset.get("safe_area") or {}
    if sa:
        sp = out.setdefault("spacing", {})
        if "top" in sa: sp["content_top"] = f"{sa['top']}px"
        if "left" in sa: sp["container_offset"] = f"{sa['left']}px"
    content = preset.get("content") or {}
    if content.get("max_width"):
        out.setdefault("spacing", {})["content_width"] = content["max_width"]
    box = preset.get("character_box") or {}
    if box:
        ly = out.setdefault("layout", {})
        if "height" in box: ly["character_height"] = f"{box['height']}px"
        if "width" in box: ly["character_box_width"] = box["width"]
    return out


def _load_template_map(figma_map_path: str | Path | None = None) -> dict:
    """Загружает карту Figma frame -> HTML template (deep merge с дефолтом)."""
    path = Path(figma_map_path) if figma_map_path else _FIGMA_TEMPLATE_MAP_PATH
    if not path.is_file():
        return dict(TEMPLATE_MAP)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            return _deep_merge(dict(TEMPLATE_MAP), loaded)
    except json.JSONDecodeError as e:
        logger.warning("Не удалось прочитать карту шаблонов %s: %s", path, e)
    return dict(TEMPLATE_MAP)


def _tokens_to_css(tokens: dict) -> str:
    """Преобразует токены Figma/бренда и preset в CSS custom properties."""
    colors = tokens.get("colors", {})
    frame_size = tokens.get("frame_size", {})
    spacing = tokens.get("spacing", {})
    layout = tokens.get("layout", {})
    radii = tokens.get("radii", {})
    shadows = tokens.get("shadows", {})
    typography = tokens.get("typography", {})

    # Обратная совместимость со старым плоским JSON.
    primary = colors.get("primary", tokens.get("primary", "#FFE033"))
    black = colors.get("black", tokens.get("black", "#000000"))
    white = colors.get("white", tokens.get("white", "#FFFFFF"))
    slide_width = frame_size.get("width", tokens.get("slide_width", VIEWPORT["width"]))
    slide_height = frame_size.get("height", tokens.get("slide_height", VIEWPORT["height"]))

    css_vars = {
        "--yellow": primary,
        "--yellow-light": colors.get("yellow_light", "#FFF3A0"),
        "--yellow-dark": colors.get("yellow_dark", "#E6C800"),
        "--black": black,
        "--white": white,
        "--gray": colors.get("gray", "#444444"),
        "--gray-light": colors.get("gray_light", "#F5F5F5"),
        "--radius": radii.get("card", "16px"),
        "--radius-sm": radii.get("small", "10px"),
        "--shadow": shadows.get("card", "0 4px 20px rgba(0,0,0,0.10)"),
        "--shadow-heavy": shadows.get("heavy", "0 8px 32px rgba(0,0,0,0.18)"),
        "--slide-width": f"{slide_width}px" if isinstance(slide_width, int) else str(slide_width),
        "--slide-height": f"{slide_height}px" if isinstance(slide_height, int) else str(slide_height),
        "--content-top": spacing.get("content_top", "60px"),
        "--content-offset": spacing.get("container_offset", "40px"),
        "--content-width": spacing.get("content_width", "580px"),
        "--character-height": layout.get("character_height", "980px"),
        "--font-family-base": typography.get("font_family", "'Inter', sans-serif"),
        "--title-size": typography.get("title_size", "68px"),
        "--subtitle-size": typography.get("subtitle_size", "32px"),
        "--body-size": typography.get("body_size", "30px"),
    }
    lines = [":root {"]
    lines.extend(f"  {key}: {value};" for key, value in css_vars.items())
    lines.append("}")
    return "\n".join(lines)


def _int_token(value, default: int) -> int:
    """Преобразует размер из int / '1080' / '1080px' в int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return default


def _css_size(value, default: str) -> str:
    """Преобразует размер в CSS-строку с px, если нужно."""
    if isinstance(value, int):
        return f"{value}px"
    if isinstance(value, str) and value.strip():
        return value
    return default


def _load_base_css(templates_dir: Path, tokens: dict) -> str:
    """Загружает base.css и добавляет CSS-переменные из дизайн-токенов."""
    css_path = templates_dir / "base.css"
    base_css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    tokens_css = _tokens_to_css(tokens)
    return f"{base_css}\n\n{tokens_css}".strip()


def _resolve_logo_path(tokens: dict) -> str | None:
    """Ищет логотип, экспортированный из Figma в brand assets."""
    assets = tokens.get("assets", {})
    candidates = []
    if isinstance(assets, dict) and assets.get("logo"):
        candidates.append(_KARUSEL_ROOT / assets["logo"])
    candidates.append(_DEFAULT_LOGO_PATH)
    for path in candidates:
        resolved = path.resolve()
        if resolved.is_file():
            return resolved.as_uri()
    return None


def _build_layout(tokens: dict, slide_type: str, template_meta: dict) -> dict:
    """Собирает layout-переменные для шаблонов из токенов Figma."""
    frame_size = tokens.get("frame_size", {})
    spacing = tokens.get("spacing", {})
    typography = tokens.get("typography", {})
    layout = tokens.get("layout", {})
    per_slide = tokens.get("template_layouts", {}).get(slide_type, {})
    frame_name = template_meta.get("frame_name", slide_type)
    per_frame = tokens.get("frame_overrides", {}).get(frame_name, {})

    merged = {
        "frame_width": _css_size(
            frame_size.get("width", tokens.get("slide_width", VIEWPORT["width"])),
            f"{VIEWPORT['width']}px",
        ),
        "frame_height": _css_size(
            frame_size.get("height", tokens.get("slide_height", VIEWPORT["height"])),
            f"{VIEWPORT['height']}px",
        ),
        "content_top": spacing.get("content_top", "60px"),
        "content_offset": spacing.get("container_offset", "40px"),
        "content_width": spacing.get("content_width", "580px"),
        "column_gap": spacing.get("column_gap", "20px"),
        "character_height": layout.get("character_height", "980px"),
        "character_bottom": layout.get("character_bottom", "0px"),
        "character_edge_offset": layout.get("character_edge_offset", "-20px"),
        "overlay_opacity": layout.get("overlay_opacity", "0.82"),
        "phone_note": layout.get("phone_note", "Напиши в директ"),
        "phone_note_size": typography.get("phone_note_size", "24px"),
        "cta_phone_size": layout.get("cta_phone_size", "42px"),
        "cta_phone_padding": layout.get("cta_phone_padding", "30px"),
        "icon_size": layout.get("icon_size", "64px"),
        "icon_gap": layout.get("icon_gap", "16px"),
        "content_side": template_meta.get("content_side", "right"),
        "character_side": template_meta.get("character_side", "right"),
        "frame_name": frame_name,
        "template_name": template_meta.get("template", f"{slide_type}.html"),
    }
    merged.update(per_slide)
    merged.update(per_frame)
    return merged


def _slide_to_context(
    slide: dict,
    brand: dict,
    base_css: str = "",
    tokens: dict | None = None,
    template_map: dict | None = None,
) -> dict:
    """Готовит контекст для Jinja: пути к картинкам как file:// для Playwright."""
    tokens = tokens or {}
    template_map = template_map or TEMPLATE_MAP
    slide_type = slide.get("type", "benefits")
    template_meta = template_map.get(slide_type, TEMPLATE_MAP["benefits"])
    layout = _build_layout(tokens, slide_type, template_meta)
    character_position = slide.get("character_position", layout["character_side"])
    ctx = {
        "base_css": base_css,
        "title": slide.get("title", ""),
        "subtitle": slide.get("subtitle", ""),
        "bullets": slide.get("bullets", []),
        "closing_line": slide.get("closing_line", ""),
        "phone": brand.get("phone", ""),
        "character_position": character_position,
        "character_path": None,
        "photo_path": None,
        "icons": slide.get("icons", []),
        "logo_path": _resolve_logo_path(tokens),
        "layout": layout,
        "figma_frame_name": layout["frame_name"],
        "template_name": layout["template_name"],
    }
    if slide.get("character_png"):
        p = Path(slide["character_png"]).resolve()
        ctx["character_path"] = p.as_uri()
    # Путь к фото для слайда (bg_photo для обложки, photo_path для photo_raw)
    for key in ("photo_path", "bg_photo"):
        if slide.get(key):
            p = Path(slide[key]).resolve()
            if p.is_file():
                ctx["photo_path"] = p.as_uri()
                break
    # Иконки для слайда target — пути как file:// URI
    icons = slide.get("icons") or []
    ctx["icons"] = [Path(ic).resolve().as_uri() for ic in icons if Path(ic).is_file()]
    return ctx


async def build_one_slide(
    browser,
    slide_data: dict,
    brand: dict,
    template_name: str,
    output_path: str | Path,
    templates_dir: Path,
    base_css: str,
    viewport: dict[str, int],
    tokens: dict | None = None,
    template_map: dict | None = None,
) -> str:
    """Рендерит один слайд в JPG."""
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template(template_name)
    ctx = _slide_to_context(
        slide_data,
        brand,
        base_css,
        tokens=tokens,
        template_map=template_map,
    )
    html_content = template.render(**ctx)
    page = await browser.new_page(viewport=viewport)
    try:
        await page.set_content(html_content, wait_until="networkidle")
        await page.screenshot(path=str(output_path), type="jpeg", quality=JPEG_QUALITY)
        return str(output_path)
    finally:
        await page.close()


async def build_carousel_async(
    slides_data: list[dict],
    brand: dict,
    output_dir: str | Path,
    templates_dir: Path | None = None,
    design_tokens_path: str | Path | None = None,
    figma_map_path: str | Path | None = None,
    preset_path: str | Path | None = None,
) -> list[str]:
    """
    Собирает все слайды параллельно. Возвращает список путей к JPG.
    slides_data: список dict с полями type, title, subtitle, bullets, character_png, и т.д.
    preset_path: опциональный render profile (config/presets/*.json) — размер, safe area, export.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = templates_dir or _TEMPLATES_DIR
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"Папка шаблонов не найдена: {templates_dir}")

    brand_dict = brand if isinstance(brand, dict) else getattr(brand, "model_dump", lambda: brand)()
    if hasattr(brand_dict, "model_dump"):
        brand_dict = brand_dict.model_dump()

    preset = _load_preset(preset_path)
    tokens = _load_design_tokens(design_tokens_path)
    preset_tokens = _preset_to_tokens(preset)
    tokens = _deep_merge(tokens, preset_tokens)
    template_map = _load_template_map(figma_map_path)
    base_css = _load_base_css(templates_dir, tokens)
    # Viewport из preset или токенов
    vp = preset.get("viewport") or tokens.get("frame_size") or {}
    viewport = {
        "width": _int_token(vp.get("width") or tokens.get("slide_width") or VIEWPORT["width"], VIEWPORT["width"]),
        "height": _int_token(vp.get("height") or tokens.get("slide_height") or VIEWPORT["height"], VIEWPORT["height"]),
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            tasks = []
            for i, slide in enumerate(slides_data):
                slide_type = slide.get("type", "benefits")
                template_meta = template_map.get(slide_type, TEMPLATE_MAP["benefits"])
                template_file = template_meta.get("template", "benefits.html")
                out_path = output_dir / f"slide_{i:02d}.jpg"
                tasks.append(
                    build_one_slide(
                        browser,
                        slide,
                        brand_dict,
                        template_file,
                        out_path,
                        templates_dir,
                        base_css,
                        viewport,
                        tokens,
                        template_map,
                    )
                )
            paths = await asyncio.gather(*tasks)
            return list(paths)
        finally:
            await browser.close()


def build_carousel(
    slides_data: list[dict],
    brand: dict,
    output_dir: str | Path,
    templates_dir: Path | None = None,
    design_tokens_path: str | Path | None = None,
    figma_map_path: str | Path | None = None,
    preset_path: str | Path | None = None,
) -> list[str]:
    """Синхронная обёртка над build_carousel_async."""
    return asyncio.run(
        build_carousel_async(
            slides_data,
            brand,
            output_dir,
            templates_dir,
            design_tokens_path,
            figma_map_path,
            preset_path,
        )
    )


if __name__ == "__main__":
    # Мини-тест: один слайд без персонажа
    test_slides = [
        {
            "type": "cover",
            "title": "Массаж в Москве",
            "subtitle": "Центр Энтузиаст",
            "bullets": ["Расслабление", "Здоровье спины", "Профессиональные руки"],
            "closing_line": "Запишись уже сегодня",
            "character_position": "right",
            "character_png": None,
        }
    ]
    test_brand = {"name": "Центр Энтузиаст", "city": "Москва", "phone": "+7 999 123-45-67", "service": "Массаж"}
    out = _KARUSEL_ROOT / "output_test"
    paths = build_carousel(test_slides, test_brand, out)
    print("Слайды:", paths)
