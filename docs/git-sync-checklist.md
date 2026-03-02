# Чек-лист: синхронизация с GitHub

Один и тот же порядок действий — без «думать».

---

## Шаг 1. Сохрани правки в Cursor

Ctrl+S или File → Save All.

---

## Шаг 2. Запусти (выбери способ)

**Вариант A — двойной клик по .bat:**
- `scripts/git-factory.bat` → content-factory
- `scripts/git-vps.bat` → entuziastov75-vps

**Вариант B — одна команда из PowerShell:**
```powershell
cd D:\content-factory\scripts
powershell -ExecutionPolicy Bypass -File .\git-factory.ps1
powershell -ExecutionPolicy Bypass -File .\git-vps.ps1
```

**Вариант C — с выбором проекта:**
```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\git-entuziastov.ps1"
```

---

## Шаг 3. В скрипте

1. Выбери **тип коммита**: 1 = feat, 2 = fix, 3 = docs
2. Введи **описание** (по-русски можно)

Примеры описаний:
- `обновил SEO-блоки для ЦА` → станет `feat: обновил SEO-блоки для ЦА`
- `правка REST для materials` → `fix: правка REST для materials`
- `добавить связь с entuziastov75-vps в README` → `docs: добавить связь...`

---

## Шаг 4. Скрипт делает сам

- `git add .`
- `git commit -m "тип: описание"`
- `git push origin main`

Готово. Изменения в GitHub.

---

## Автосинхронизация каждые 30 минут

1. Открой **Планировщик заданий** Windows
2. Создать задачу → Триггер: повторять каждые 30 мин
3. Действие: `powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\git-auto-sync.ps1" -project factory`
4. Рабочая папка (по желанию): `D:\content-factory`

Скрипт `git-auto-sync.ps1`:
- Делает `git status --porcelain` → при пустом результате выходит
- При изменениях вызывает `git-entuziastov.ps1` с `-type chore -message "автосинхронизация YYYY-MM-DD HH:mm"`

---

## Пути проектов

| Проект | Путь |
|--------|------|
| content-factory | `D:\content-factory` |
| entuziastov75-vps | `D:\entuziastov75-vps` или `C:\Users\user\Documents\seo_entuziastov75` (авто) |
