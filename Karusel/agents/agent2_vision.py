"""
Agent 2 — Vision: анализ фото через LLM (GPT-4o или Ollama/LLaVA).
Для каждого фото возвращает VisionResult: has_person, photo_quality, recommended_role и т.д.
"""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))

from models.carousel_schema import PhotoQuality, PhotoRole, VisionResult
from logger import get_logger

logger = get_logger("agent2_vision")

# ── Промпт ────────────────────────────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """
Ты — агент анализа фотографий для контент-завода.
Получаешь одно фото и возвращаешь СТРОГО валидный JSON без markdown.

ПРАВИЛА АНАЛИЗА:

has_person: true если на фото есть человек (врач/клиент/персонал)

person_type:
  "doctor"  — в белом халате или медицинской одежде
  "client"  — в халате пациента / обычной одежде
  "staff"   — персонал без халата
  "none"    — людей нет

person_position:
  "left" / "center" / "right" — где стоит основной персонаж
  "none" — людей нет

person_fullbody:
  true  — видно тело от головы до колен и ниже
  false — только бюст / лицо

background:
  "clinic"     — медицинский интерьер
  "studio"     — студийный фон (однотонный)
  "yellow"     — желтый фон (фирменный)
  "equipment"  — медицинское оборудование на переднем плане
  "outdoor"    — улица / природа
  "none"       — фон неопределим

orientation:
  "portrait"   — высота > ширины
  "landscape"  — ширина > высоты
  "square"     — примерно равны

photo_quality:
  "high"   — резкое, хорошая экспозиция, нет смаза
  "medium" — небольшие дефекты но годится
  "low"    — размытое / тёмное / нерезкое

main_object:
  "person"    — главное это человек
  "device"    — медицинский аппарат / оборудование
  "room"      — интерьер помещения
  "procedure" — процедура (человек + аппарат вместе)
  "none"      — неопределимо

recommended_role:
  "character"   — хорошее фото персонажа → вырезаем фон, ставим на слайд
  "raw_photo"   — фото аппарата/процедуры → вставляем целиком как слайд
  "background"  — фото интерьера → используем как фоновый слой
  "skip"        — плохое качество → игнорируем

ЛОГИКА recommended_role:
  has_person=true  + quality=high/medium + fullbody=true  → "character"
  has_person=true  + quality=low                          → "skip"
  has_person=false + main_object="device"                 → "raw_photo"
  has_person=false + main_object="room"                   → "background"
  has_person=true  + fullbody=false + quality=high        → "character"
  иначе                                                   → "raw_photo"

ФОРМАТ ОТВЕТА (только JSON, никаких пояснений):
{
  "has_person": true,
  "person_type": "doctor",
  "person_position": "center",
  "person_fullbody": true,
  "background": "clinic",
  "orientation": "portrait",
  "photo_quality": "high",
  "main_object": "person",
  "recommended_role": "character"
}
"""

# ── Вспомогательные функции ───────────────────────────────────────────────────

async def _read_image_b64(path: str) -> str:
    """Читает файл и возвращает base64-строку."""
    import aiofiles
    async with aiofiles.open(path, "rb") as f:
        raw = await f.read()
    return base64.b64encode(raw).decode("utf-8")


def _parse_vision_response(raw: str, index: int) -> VisionResult:
    """
    Парсит ответ LLM → VisionResult.
    Пробует вытащить JSON даже если есть лишний текст вокруг.
    """
    cleaned = raw.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                cleaned = p
                break
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"JSON не найден в ответе: {raw[:200]}")
    data = json.loads(cleaned[start:end])
    data["index"] = index
    return VisionResult(**data)


# ── Основной класс ────────────────────────────────────────────────────────────

class VisionAgent:
    """
    Анализирует список фото и возвращает VisionResult для каждого.
    Бэкенды: openai (GPT-4o), ollama (LLaVA локально).
    """

    def __init__(
        self,
        backend: str = "openai",
        model: str = "gpt-4o",
        api_key: str | None = None,
        ollama_url: str = "http://localhost:11434",
        max_concurrent: int = 3,
    ):
        self.backend = backend
        self.model = model
        self.api_key = api_key
        self.ollama_url = ollama_url
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze(self, photo_paths: list[str]) -> list[VisionResult]:
        """Анализирует все фото параллельно. Возвращает список VisionResult в порядке photo_paths."""
        tasks = [self._analyze_one(p, idx) for idx, p in enumerate(photo_paths)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        final: list[VisionResult] = []
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                logger.warning("Vision ошибка фото %s: %s", idx, res)
                final.append(self._fallback(idx, photo_paths[idx]))
            else:
                final.append(res)
        return final

    async def _analyze_one(self, path: str, index: int) -> VisionResult:
        async with self._semaphore:
            logger.info("Vision анализ фото %s: %s", index, Path(path).name)
            b64 = await _read_image_b64(path)
            if self.backend == "openai":
                raw = await self._call_openai(b64)
            elif self.backend == "ollama":
                raw = await self._call_ollama(b64)
            else:
                raise ValueError(f"Неизвестный backend: {self.backend}")
            return _parse_vision_response(raw, index)

    async def _call_openai(self, b64: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "low",
                            },
                        },
                        {"type": "text", "text": "Проанализируй фото и верни JSON."},
                    ],
                },
            ],
        )
        return response.choices[0].message.content or ""

    async def _call_ollama(self, b64: str) -> str:
        import aiohttp
        payload = {
            "model": self.model,
            "prompt": VISION_SYSTEM_PROMPT + "\n\nПроанализируй фото и верни JSON.",
            "images": [b64],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("response", "")

    @staticmethod
    def _fallback(index: int, path: str) -> VisionResult:
        """Если Vision не смог — определяем роль по размеру файла."""
        p = Path(path)
        size = p.stat().st_size if p.exists() else 0
        role = PhotoRole.CHARACTER if size > 100_000 else PhotoRole.RAW_PHOTO
        return VisionResult(
            index=index,
            has_person=True,
            person_type="doctor",
            person_position="center",
            person_fullbody=True,
            background="clinic",
            orientation="portrait",
            photo_quality=PhotoQuality.MEDIUM,
            main_object="person",
            recommended_role=role,
        )

    @staticmethod
    def pick_best_character(results: list[VisionResult]) -> int | None:
        """Из всех фото возвращает индекс лучшего персонажа."""
        candidates = [r for r in results if r.recommended_role == PhotoRole.CHARACTER]
        if not candidates:
            return None
        def score(r: VisionResult) -> int:
            s = 0
            if r.photo_quality == PhotoQuality.HIGH:
                s += 10
            if r.photo_quality == PhotoQuality.MEDIUM:
                s += 5
            if r.person_fullbody:
                s += 4
            if r.person_type == "doctor":
                s += 3
            if r.person_type == "client":
                s += 1
            return s
        return max(candidates, key=score).index

    @staticmethod
    def pick_background(results: list[VisionResult]) -> int | None:
        """Индекс лучшего фото для фона обложки."""
        candidates = [r for r in results if r.recommended_role == PhotoRole.BACKGROUND]
        return candidates[0].index if candidates else None

    @staticmethod
    def pick_raw_photos(results: list[VisionResult]) -> list[int]:
        """Индексы raw-фото (аппараты, процедуры)."""
        return [r.index for r in results if r.recommended_role == PhotoRole.RAW_PHOTO]


# ── Синхронная обёртка для текущего пайплайна ──────────────────────────────────

def analyze_photos(photo_paths: list[str], backend: str = "openai", model: str = "gpt-4o") -> list[VisionResult]:
    """Синхронный вызов: анализирует фото и возвращает список VisionResult."""
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "").strip() or None
    agent = VisionAgent(backend=backend, model=model, api_key=api_key)
    return asyncio.run(agent.analyze(photo_paths))
