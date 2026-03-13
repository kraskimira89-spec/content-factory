# -*- coding: utf-8 -*-
"""
Сухой прогон пресетов SD — без вызова LLM.
Показывает итоговые prompt / negative_prompt после подстановки параметров.

Запуск:
    python image-agents/agent8_prompt/test_presets.py

Опции:
    --slug massazh              # один конкретный слаг
    --params '{"age": "elderly woman, silver_hair"}'  # переопределить параметры
    --all                       # прогнать все пресеты с дефолтными params
"""
import json
import sys
import argparse
from pathlib import Path

_CURRENT     = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT.parent.parent

# Добавляем пути до импорта модулей проекта
sys.path.insert(0, str(_CURRENT))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "seo-agents"))

# Импортируем только утилиты пресетов — без цепочки AI-импортов
import importlib.util as _ilu

def _import_preset_utils():
    """Импортирует только функции работы с пресетами из agent8_prompt.py."""
    spec = _ilu.spec_from_file_location("_a8", _CURRENT / "agent8_prompt.py")
    # Патчим заглушками AI-зависимости, чтобы не падал импорт
    import unittest.mock as _mock
    with _mock.patch.dict("sys.modules", {
        "shared.api_client": _mock.MagicMock(),
        "scripts.shared_config": _mock.MagicMock(),
    }):
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod

_m = _import_preset_utils()
load_presets  = _m.load_presets
get_preset    = _m.get_preset
apply_params  = _m.apply_params

import io, sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

SEP = "-" * 72


def check_prompt_quality(prompt: str) -> list[str]:
    """Простые эвристики: нет предложений, нет лишних запятых."""
    issues = []
    # Предложения (слова-связки) — игнорируем устойчивые SD-конструкции
    SD_ALLOWED = {"before and after", "and after", "black and white"}
    sentence_words = [" who ", " which ", " while ", " with her ", " with his ", " is lying ", " are "]
    prompt_lower = prompt.lower()
    for w in sentence_words:
        if w in prompt_lower and not any(a in prompt_lower for a in SD_ALLOWED):
            issues.append(f"possible sentence word: '{w.strip()}'")
    # Пустые двойные запятые
    if ",," in prompt or ", ," in prompt:
        issues.append("⚠  двойная запятая (пустой тег)")
    # Начало/конец с запятой
    if prompt.startswith(",") or prompt.endswith(","):
        issues.append("⚠  промпт начинается или заканчивается запятой")
    # Незамещённые плейсхолдеры
    import re
    unresolved = re.findall(r"\{[a-z_]+\}", prompt)
    if unresolved:
        issues.append(f"⚠  незамещённые плейсхолдеры: {unresolved}")
    return issues


def run_preset(preset: dict, overrides: dict) -> None:
    params_spec = preset.get("params", {})
    prompt = apply_params(preset["base_prompt"], params_spec, overrides)
    neg    = preset["base_negative_prompt"]
    sd     = preset.get("sd_params", {})

    print(SEP)
    print(f"  id:           {preset['id']}")
    print(f"  title:        {preset['title']}")
    print(f"  service_type: {preset['service_type']}")
    print(f"  aspect_ratio: {preset.get('aspect_ratio','')}")
    print()
    print(f"  PROMPT ({len(prompt.split(','))} тегов):")
    print(f"    {prompt}")
    print()
    print(f"  NEGATIVE ({len(neg.split(','))} тегов):")
    print(f"    {neg}")
    print()
    if sd:
        print(f"  SD PARAMS:  steps={sd.get('steps')}  cfg={sd.get('cfg_scale')}  "
              f"sampler={sd.get('sampler')}  {sd.get('width')}×{sd.get('height')}")
    issues = check_prompt_quality(prompt)
    if issues:
        print()
        for issue in issues:
            print(f"  [!] {issue}")
    else:
        print("  [OK] промпт чистый")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run пресетов SD без LLM")
    parser.add_argument("--slug",   default="",   help="Слаг услуги (напр. massazh)")
    parser.add_argument("--params", default="{}",  help="JSON параметров для подстановки")
    parser.add_argument("--all",    action="store_true", help="Прогнать все пресеты")
    args = parser.parse_args()

    overrides = json.loads(args.params)
    data      = load_presets()
    presets   = data.get("image_presets", [])

    if not presets:
        print("Пресеты не найдены. Проверь prompts/image_presets.json")
        sys.exit(1)

    print(f"\n{'='*72}")
    print("  TEST PRESETS -- dry run (bez LLM)")
    print(f"{'='*72}")

    if args.all or not args.slug:
        for preset in presets:
            run_preset(preset, overrides)
    else:
        preset = get_preset(args.slug)
        if not preset:
            print(f"Пресет для слага «{args.slug}» не найден.")
            mapping = data.get("service_to_preset", {})
            print(f"Доступные слаги: {', '.join(mapping.keys())}")
            sys.exit(1)
        run_preset(preset, overrides)

    print(SEP)
    print(f"  Итого пресетов: {len(presets)}")
    print(SEP + "\n")


if __name__ == "__main__":
    main()
