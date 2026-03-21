"""
Agent 3b — генерация персонажа через ComfyUI (опционально), затем rembg.
Включается CHAR_VARIATION_ENABLED=1. Приоритет в composer: AI > rembg.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

_AGENTS_DIR = Path(__file__).resolve().parent
_KARUSEL_ROOT = _AGENTS_DIR.parent
if str(_KARUSEL_ROOT) not in sys.path:
    sys.path.insert(0, str(_KARUSEL_ROOT))

from logger import get_logger

logger = get_logger("agent3b_chargen")

_PRESETS_PATH = _KARUSEL_ROOT / "config" / "character_variation_presets.json"


def is_chargen_enabled() -> bool:
    return os.environ.get("CHAR_VARIATION_ENABLED", "").strip().lower() in ("1", "true", "yes")


def is_char_on_every_slide() -> bool:
    """Если не задано — False (обратная совместимость). При CHAR_VARIATION_ENABLED=1 обычно ставят True."""
    raw = os.environ.get("CHAR_ON_EVERY_SLIDE", "").strip().lower()
    if not raw:
        return False
    return raw in ("1", "true", "yes")


def _load_presets() -> dict[str, Any]:
    if not _PRESETS_PATH.is_file():
        return {}
    with open(_PRESETS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _slide_type_str(slide) -> str:
    t = getattr(slide, "type", "benefits")
    if hasattr(t, "value"):
        return str(t.value)
    return str(t)


class CharGenAgent:
    """Генерация PNG персонажа на слайд через ComfyUI API + rembg."""

    def __init__(self, presets: dict[str, Any] | None = None):
        self.presets = presets or _load_presets()
        comfy = self.presets.get("comfyui", {})
        self.host = (
            os.environ.get("COMFYUI_URL", "").strip().rstrip("/")
            or comfy.get("host", "http://127.0.0.1:8188").rstrip("/")
        )
        wf_rel = comfy.get("workflow_path", "assets/carousel/comfyui_portrait.json")
        self.workflow_path = _KARUSEL_ROOT / wf_rel.replace("/", os.sep)
        self.checkpoint = os.environ.get("COMFYUI_CHECKPOINT", "").strip() or comfy.get(
            "checkpoint_name", "realisticVision_v60B1VAE.safetensors"
        )
        self.poll_interval = float(comfy.get("poll_interval_sec", 1.5))
        self.poll_timeout = float(comfy.get("poll_timeout_sec", 120))
        self.max_concurrent = int(comfy.get("max_concurrent", 2))
        self.width = int(comfy.get("width", 512))
        self.height = int(comfy.get("height", 768))
        self.steps = int(comfy.get("steps", 22))
        self.cfg = float(comfy.get("cfg", 7.0))
        self.sampler_name = str(comfy.get("sampler_name", "dpmpp_2m"))
        self.scheduler = str(comfy.get("scheduler", "karras"))
        self._sem = asyncio.Semaphore(self.max_concurrent)

    def _should_generate_slide(self, slide) -> bool:
        st = _slide_type_str(slide)
        skip = set(self.presets.get("skip_slide_types", ["photo_raw", "cta"]))
        if st in skip:
            return False
        if is_char_on_every_slide():
            return True
        return bool(getattr(slide, "use_character", False))

    def _build_prompts(self, slide, brand) -> tuple[str, str]:
        st = _slide_type_str(slide)
        pose_map = self.presets.get("pose_by_slide_type", {})
        pose_data = pose_map.get(st) or pose_map.get("benefits") or {}
        base_pos = self.presets.get("base_positive", "")
        base_neg = self.presets.get("base_negative", "")
        parts = [
            base_pos,
            pose_data.get("pose", ""),
            pose_data.get("expression", ""),
            pose_data.get("clothing", ""),
            pose_data.get("background", ""),
        ]
        brand_bits = []
        if brand:
            bd = brand.model_dump() if hasattr(brand, "model_dump") else dict(brand)
            if bd.get("service"):
                brand_bits.append(f"context: {bd['service']}")
            if bd.get("city"):
                brand_bits.append(f"city: {bd['city']}")
        if brand_bits:
            parts.append(", ".join(brand_bits))
        positive = ", ".join(p for p in parts if p and str(p).strip())
        negative = base_neg.strip()
        return positive, negative

    def _patch_workflow(self, workflow: dict, positive: str, negative: str, seed: int) -> None:
        """Патчит ноды по class_type и известным id из comfyui_portrait.json."""
        for _nid, node in workflow.items():
            if not isinstance(node, dict):
                continue
            ct = node.get("class_type")
            inputs = node.setdefault("inputs", {})
            if ct == "KSampler":
                inputs["seed"] = seed
                inputs["steps"] = self.steps
                inputs["cfg"] = self.cfg
                inputs["sampler_name"] = self.sampler_name
                inputs["scheduler"] = self.scheduler
            elif ct == "EmptyLatentImage":
                inputs["width"] = self.width
                inputs["height"] = self.height
            elif ct == "CheckpointLoaderSimple":
                inputs["ckpt_name"] = self.checkpoint

        # Явные плейсхолдеры и стандартные id из comfyui_portrait.json
        for _nid, node in workflow.items():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs") or {}
            if inputs.get("text") == "POSITIVE_PLACEHOLDER":
                inputs["text"] = positive
            if inputs.get("text") == "NEGATIVE_PLACEHOLDER":
                inputs["text"] = negative
        if "6" in workflow and workflow["6"].get("class_type") == "CLIPTextEncode":
            workflow["6"].setdefault("inputs", {})["text"] = positive
        if "7" in workflow and workflow["7"].get("class_type") == "CLIPTextEncode":
            workflow["7"].setdefault("inputs", {})["text"] = negative

    async def _comfyui_generate_bytes(self, positive: str, negative: str, seed: int) -> bytes:
        if not self.workflow_path.is_file():
            raise FileNotFoundError(f"ComfyUI workflow не найден: {self.workflow_path}")

        with open(self.workflow_path, encoding="utf-8") as f:
            workflow = json.loads(f.read())
        workflow = copy.deepcopy(workflow)
        self._patch_workflow(workflow, positive, negative, seed)

        import aiohttp

        client_id = f"karusel_{random.randint(10000, 99999)}"
        payload = {"prompt": workflow, "client_id": client_id}

        timeout = aiohttp.ClientTimeout(total=self.poll_timeout + 30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.host}/prompt", json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
            prompt_id = data.get("prompt_id")
            if not prompt_id:
                raise RuntimeError(f"ComfyUI /prompt: нет prompt_id: {data}")

            elapsed = 0.0
            while elapsed < self.poll_timeout:
                await asyncio.sleep(self.poll_interval)
                elapsed += self.poll_interval
                async with session.get(f"{self.host}/history/{prompt_id}") as hresp:
                    if hresp.status != 200:
                        continue
                    history = await hresp.json()
                entry = history.get(prompt_id) if isinstance(history, dict) else None
                if not entry:
                    continue
                outputs = entry.get("outputs") or {}
                for _node_id, node_out in outputs.items():
                    images = node_out.get("images") or []
                    for img_info in images:
                        filename = img_info.get("filename")
                        if not filename:
                            continue
                        subfolder = img_info.get("subfolder", "")
                        folder_type = img_info.get("type", "output")
                        params = f"filename={filename}&type={folder_type}"
                        if subfolder:
                            params += f"&subfolder={subfolder}"
                        async with session.get(f"{self.host}/view?{params}") as img_resp:
                            img_resp.raise_for_status()
                            return await img_resp.read()

            raise TimeoutError(f"ComfyUI: таймаут {self.poll_timeout}s, prompt_id={prompt_id}")

    async def _generate_one(self, slide, brand, chars_dir: Path) -> str | None:
        slide_id = getattr(slide, "id", 0)
        async with self._sem:
            positive, negative = self._build_prompts(slide, brand)
            seed = random.randint(0, 2**31 - 1)
            logger.info("CharGen: слайд id=%s seed=%s", slide_id, seed)
            try:
                png_bytes = await self._comfyui_generate_bytes(positive, negative, seed)
            except Exception as e:
                logger.error("CharGen ComfyUI слайд %s: %s", slide_id, e)
                return None

            raw_path = chars_dir / f"_comfy_raw_slide_{slide_id:02d}.png"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(png_bytes)

            final = await asyncio.to_thread(self._rembg_png_sync, raw_path, chars_dir)
            if final:
                target = chars_dir / f"char_slide_{slide_id:02d}.png"
                try:
                    import shutil
                    shutil.copy2(final, target)
                    return str(target.resolve())
                except Exception as e:
                    logger.warning("CharGen копирование финала: %s", e)
                    return str(Path(final).resolve())
            return None

    def _rembg_png_sync(self, raw_png_path: Path, chars_dir: Path) -> str | None:
        from agents.agent3_rembg import process_photo_for_character, RembgAgent

        try:
            out = process_photo_for_character(raw_png_path, output_dir=chars_dir)
            if RembgAgent.validate_output(out):
                return out
        except Exception as e:
            logger.warning("CharGen rembg sync %s: %s", raw_png_path.name, e)
        return None

    async def generate_all(self, carousel_data, output_dir: str | Path) -> dict[int, str]:
        """
        Возвращает {slide.id: path_png} только для успешных генераций.
        """
        out_dir = Path(output_dir)
        chars_dir = out_dir / "chars"
        chars_dir.mkdir(parents=True, exist_ok=True)
        brand = carousel_data.brand
        slides = [
            s for s in carousel_data.slides if self._should_generate_slide(s)
        ]
        if not slides:
            logger.info("CharGen: нет слайдов для генерации")
            return {}

        tasks = [self._generate_one(s, brand, chars_dir) for s in slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        char_map: dict[int, str] = {}
        for slide, result in zip(slides, results):
            sid = getattr(slide, "id", 0)
            if isinstance(result, Exception):
                logger.error("CharGen слайд %s: %s", sid, result)
                continue
            if result and Path(result).is_file():
                char_map[sid] = result
        logger.info("CharGen: готово %s/%s слайдов", len(char_map), len(slides))
        return char_map


def run_chargen_sync(carousel_data, output_dir: str | Path) -> dict[int, str]:
    """Синхронная обёртка для run_pipeline."""
    if not is_chargen_enabled():
        return {}
    agent = CharGenAgent()
    return asyncio.run(agent.generate_all(carousel_data, output_dir))


async def run_chargen_async(carousel_data, output_dir: str | Path) -> dict[int, str]:
    if not is_chargen_enabled():
        return {}
    agent = CharGenAgent()
    return await agent.generate_all(carousel_data, output_dir)
