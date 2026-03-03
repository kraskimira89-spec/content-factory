# Чередование текста и картинок на страницах услуг

**Дата:** 2025-03-03  
**Цель:** избежать «стены текста» в начале страницы; визуально и эмоционально поддерживать контент.

---

## Текущее состояние

- Hero-картинка — одна, в шапке.
- Встраиваемые картинки — после первого абзаца (все подряд).
- Agent8 — заглушка, 1 generic-промпт без привязки к смыслу блоков.

---

## Целевая схема

| Вариант | Описание |
|---------|----------|
| A | Текст слева, картинка справа → картинка слева, текст справа (чередование) |
| B | Два блока текста, под ними одна картинка |
| C | Один блок текста, под ним картинка, следующий блок текста, картинка |

**Привязка:** каждая картинка привязана к H2-блоку (после какого блока вставить).

---

## Роль Agent3

После каждого H2 вставлять `<!-- image_slot: SLOT -->` (problems, mechanism, result, target_audience, procedure, faq, utp). Комментарии сохраняются в HTML.

## Роль Agent8

1. **Парсинг** markdown по `<!-- image_slot: X -->` — извлекает блоки {slot, title, text}.
2. **Для каждого слота** — отдельный вызов AI с контекстом блока (не страница целиком).
3. **Эмоциональные промпты** по смыслу слота: problems→тяжёлые ноги/усталость, mechanism→схема движения, procedure→спокойная сцена, result→лёгкость, utp→атмосфера центра.
4. **Выдача** `images: [{ slot, prompt, alt, layout }]`. Fallback: без слотов — по insert_after_block.

---

## Контракт (расширение image_protocol)

**Слоты в markdown:** после каждого H2 — `<!-- image_slot: SLOT -->`. Слоты: problems, mechanism, result, target_audience, process, faq, utp.

```json
{
  "images": [
    {
      "slot": "problems",
      "prompt": "...",
      "style": "realistic photo",
      "alt": "...",
      "layout": "right",
      "role": "emotion_support"
    }
  ]
}
```

- **slot:** привязка к `<!-- image_slot: X -->` в markdown (приоритет над insert_after_block).
- **insert_after_block:** fallback, когда слотов нет (0 = после лида, 1 = первый H2, …).
- **layout:** `left` | `right` | `below` — картинка слева, справа, или блоком под текстом.

---

## Agent4

Приоритет вставки: `slot` (по `<!-- image_slot: X -->`) → `insert_after_block` → после первого `</p>`.
- **_embed_images_by_slots:** ищет `<!-- image_slot: X -->`, вставляет figure с matching slot.
- **_embed_images_by_blocks:** fallback по H2, когда слотов нет.

---

## Шаги реализации

1. [x] Промпт agent8: «извлеки смысл, создай символичный промпт»
2. [x] agent8: парсинг H2, вызов AI, output с insert_after_block и layout
3. [x] shared-config: расширить fields (insert_after_block, layout)
4. [x] agent4: вставка по блокам с layout
5. [x] agent9: поддержка нового формата (без изменений, index = порядок)
