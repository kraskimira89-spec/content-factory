# Тесты Karusel

## Ручной сценарий Vision + Rembg

Файл [`test_agents_2_3.py`](test_agents_2_3.py) — **не** pytest-тест: это скрипт, запускаемый явно:

```powershell
cd D:\content-factory\Karusel
python tests\test_agents_2_3.py
```

Или через GPU-обёртку: [`Karusel/run-test-agents-2-3-gpu.ps1`](../run-test-agents-2-3-gpu.ps1).

Нужны фото в `Karusel/temp/test/photo_0.jpg` и при желании `photo_1.jpg` (см. комментарии в начале скрипта). Без них скрипт завершится с подсказкой.

## Приоритет персонажа (CharGen vs rembg)

[`test_chargen_compose.py`](test_chargen_compose.py) — проверка логики `compose_slides` (AI-путь vs rembg), запуск:

```powershell
python tests\test_chargen_compose.py
```

## Pytest

Имя файла `test_*.py` может вводить в заблуждение: для коллекции pytest внутри должны быть функции `test_*` или классы `Test*`. Сейчас их нет — **`pytest` этот файл не выполняет как тесты**.
