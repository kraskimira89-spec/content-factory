# Идеальный цикл: правка текста → публикация

Последний шаг — **всегда через Agent 7**, а не напрямую Agent 4. Так текст всегда берётся из `materials/pages_manual/`.

---

## Для Прессотерапии

1. Открой `materials/pages_manual/pressoterapiya.md`
2. Читай, меняй заголовки (H1, H2), структуру блоков
3. Подправляй текст по смыслу: болевая, как проходит, результаты, противопоказания, призыв
4. Сохрани файл
5. В PowerShell:

```powershell
cd D:\content-factory
$env:PYTHONIOENCODING = "utf-8"
python seo-agents\agent7_manual_publish\agent_7_manual_publish.py pressoterapiya
```

6. Открой http://91.229.11.147/uslugi/pressoterapiya/ и проверь: H1/H2 и структура совпадают с .md

---

## Для Соляной комнаты

То же самое, только:
- Файл: `materials/pages_manual/solyanaya-komnata.md`
- Slug: `solyanaya-komnata`
- URL: http://91.229.11.147/uslugi/solyanaya-komnata/

```powershell
python seo-agents\agent7_manual_publish\agent_7_manual_publish.py solyanaya-komnata
```

---

## Что делает Agent 7

1. Копирует `materials/pages_manual/{slug}.md` → `output/*_page_*.md`
2. Запускает Agent 4 для публикации в WordPress

Цены, карточки, кнопки — из шаблона и `services_data` на VPS, редактируются отдельно.
