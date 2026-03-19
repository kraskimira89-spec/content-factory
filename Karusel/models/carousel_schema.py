"""
Pydantic-модели для пайплайна карусели.
Выход Agent 1 (Parser) → CarouselData. Vision → VisionResult. Composer → RenderData.
"""
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Строковые алиасы (совместимость с Parser/Composer) ───
SlideTypeStr = Literal[
    "cover", "benefits", "indications", "howworks",
    "target", "results", "photo_raw", "cta",
]
CharacterPositionStr = Literal["left", "right"]


# ─── Энумы (спека) ─────────────────────────────────────────
class SlideType(str, Enum):
    COVER = "cover"
    BENEFITS = "benefits"
    INDICATIONS = "indications"
    HOW_WORKS = "howworks"
    TARGET_AUDIENCE = "target"
    RESULTS = "results"
    PHOTO_RAW = "photo_raw"
    CTA = "cta"


class CharPosition(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


class PhotoRole(str, Enum):
    CHARACTER = "character"
    RAW_PHOTO = "raw_photo"
    BACKGROUND = "background"
    SKIP = "skip"


class PhotoQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ─── Vision (Agent 2) ───────────────────────────────────────
class VisionResult(BaseModel):
    index: int
    has_person: bool = False
    person_type: Literal["doctor", "client", "staff", "none"] = "none"
    person_position: Literal["left", "center", "right", "none"] = "none"
    person_fullbody: bool = False
    background: Literal["clinic", "studio", "yellow", "equipment", "outdoor", "none"] = "none"
    orientation: Literal["portrait", "landscape", "square"] = "portrait"
    photo_quality: PhotoQuality = PhotoQuality.MEDIUM
    main_object: Literal["person", "device", "room", "procedure", "none"] = "none"
    recommended_role: PhotoRole = PhotoRole.SKIP


# ─── Бренд ──────────────────────────────────────────────────
class Brand(BaseModel):
    name: str = ""
    city: str = ""
    phone: str = ""
    service: str = ""


class BrandData(BaseModel):
    """Бренд с цветами."""
    name: str = ""
    city: str = ""
    phone: str = ""
    service: str = ""
    color_primary: str = "#FFE033"
    color_text: str = "#000000"
    color_bg: str = "#FFFFFF"


# ─── Слайд (Parser → Composer) ──────────────────────────────
class SlideData(BaseModel):
    id: int = Field(ge=1)
    type: SlideTypeStr
    title: str = ""
    subtitle: str = ""
    bullets: list[str] = Field(default_factory=list)
    closing_line: str = ""
    photo_index: int = 0
    use_character: bool = False
    character_position: CharacterPositionStr = "right"
    need_icons: bool = False

    icon_hints: list[str] = Field(default_factory=list)
    character_png: Optional[str] = None
    bg_photo: Optional[str] = None
    icons: list[str] = Field(default_factory=list)

    @field_validator("character_position", mode="before")
    @classmethod
    def empty_position_to_right(cls, v: str | None) -> str:
        """Пустая строка или None от LLM → по умолчанию 'right'."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return "right"
        return v


# ─── Полная карусель (Parser) ───────────────────────────────
class CarouselData(BaseModel):
    brand: Brand
    slides: list[SlideData] = Field(default_factory=list, max_length=10)


# ─── Данные для рендера одного слайда (Composer → Builder) ─
class RenderData(BaseModel):
    slide_id: int
    slide_type: str
    template_name: str
    title: str = ""
    subtitle: str = ""
    bullets: list[str] = Field(default_factory=list)
    closing_line: Optional[str] = None
    phone: str = ""
    brand_name: str = ""
    character_png: Optional[str] = None
    character_side: str = "right"
    bg_photo: Optional[str] = None
    icons: list[str] = Field(default_factory=list)
    color_primary: str = "#FFE033"
    color_text: str = "#000000"
    color_bg: str = "#FFFFFF"


# ─── Контекст сессии (FSM / temp) ────────────────────────────
class SessionData(BaseModel):
    session_id: str = ""
    user_id: int = 0
    photo_paths: list[str] = Field(default_factory=list)
    raw_text: str = ""
    vision_results: list[VisionResult] = Field(default_factory=list)
    carousel_json: Optional[CarouselData] = None
    char_png_path: Optional[str] = None
    render_queue: list[RenderData] = Field(default_factory=list)
    slide_paths: list[str] = Field(default_factory=list)
