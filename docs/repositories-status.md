# Статус репозиториев

Дата проверки: 2025-03-01 (обновлено: единый workspace)

---

## 1. content-factory ✅

| Параметр | Значение |
|----------|----------|
| **Путь** | `D:\content-factory` |
| **Remote** | `https://github.com/kraskimira89-spec/content-factory.git` |
| **Ветка** | main |
| **Статус** | Чистое дерево, синхронизировано с origin |

**Проверка:** репозиторий доступен на GitHub, структура в порядке.

---

## 2. entuziastov75-vps ✅

| Параметр | Значение |
|----------|----------|
| **Путь** | `C:\Users\user\Documents\seo_entuziastov75` |
| **Remote** | `https://github.com/kraskimira89-spec/entuziastov75-vps.git` |
| **Ветка** | main |
| **Статус** | Синхронизируется с GitHub |

### Единое рабочее пространство

Workspace: `d:\content-and-vps\content-factory.code-workspace`

```json
{
  "folders": [
    { "path": "../content-factory", "name": "content-factory" },
    { "path": "C:/Users/user/Documents/seo_entuziastov75", "name": "entuziastov75-vps" }
  ]
}
```

**Открыть:** File → Open Workspace from File… → `D:\content-and-vps\content-factory.code-workspace`

Оба репо в одной панели — правки и push из одного окна Cursor.

**Автоматизация с GitHub (Actions + Планировщик):** см. **`docs/github-automation.md`**.

---

## 3. Синхронизация из единого workspace

1. **Открыть workspace:** File → Open Workspace from File… → `D:\content-and-vps\content-factory.code-workspace`
2. В боковой панели видны две папки: **content-factory** и **entuziastov75-vps**.
3. Для каждого репо: `Source Control` (Ctrl+Shift+G) → выбрать репо → Commit & Push.

### Remote-SSH (для VPS)

Работа с файлами на сервере: `Ctrl+Shift+P` → Remote-SSH: Connect to Host → `root@91.229.11.147` → Open Folder `/root/sites/entuziastov75VPS`. Подробно: **`docs/remote-ssh-vps.md`**

---

## 4. Сводка

| Репо | Локально | GitHub | Workspace |
|------|----------|--------|-----------|
| content-factory | `D:\content-factory` | ✅ | content-factory |
| entuziastov75-vps | `C:\Users\user\Documents\seo_entuziastov75` | ✅ | entuziastov75-vps |

Оба в workspace `content-factory.code-workspace` — синхронизация с GitHub из единого окна.
