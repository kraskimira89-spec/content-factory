# Автоматизация с GitHub для двух папок

Описывает настройку синхронизации и CI для **content-factory** и **entuziastov75-vps** (папка seo_entuziastov75).

---

## 1. content-factory (папка в workspace)

| Что | Где | Описание |
|-----|-----|----------|
| **GitHub Actions** | `.github/workflows/scheduled.yml` | Запуск при **push в main**, по **cron каждые 6 ч** и вручную (workflow_dispatch). Проверка зависимостей и импорта Karusel. |
| **Локальная автосинхронизация** | Планировщик Windows | Задача **GitSyncContentFactory** — каждые 30 мин: при наличии изменений выполняется `git-entuziastov.ps1 -project factory`. |

**Включить локальную задачу (один раз):**
```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\register-git-sync-tasks.ps1"
```
Скрипт создаёт задачи для **обеих** папок (factory и vps).

---

## 2. entuziastov75-vps (папка seo_entuziastov75)

| Что | Где | Описание |
|-----|-----|----------|
| **GitHub Actions** | `C:\...\seo_entuziastov75\.github\workflows\deploy.yml` | **Deploy to VPS** — при push в main выполняется деплой на сервер по SSH (git fetch + reset). Нужны секреты: SSH_HOST, SSH_USER, SSH_PRIVATE_KEY, DEPLOY_PATH. |
| **Локальная автосинхронизация** | Планировщик Windows | Задача **GitSyncEntuziastov75Vps** — каждые 30 мин: при изменениях выполняется `git-auto-sync.ps1 -project vps`. |

Репозиторий на GitHub: `https://github.com/kraskimira89-spec/entuziastov75-vps`

---

## 3. Восстановление автоматизации

1. **GitHub Actions** уже настроены:
   - content-factory: workflow в `d:\content-factory\.github\workflows\scheduled.yml`
   - entuziastov75-vps: workflow в корне репо `seo_entuziastov75\.github\workflows\deploy.yml`

2. **Планировщик Windows** (автосинхронизация каждые 30 мин для обеих папок):
   ```powershell
   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\register-git-sync-tasks.ps1"
   ```
   Проверка: `taskschd.msc` → задачи **GitSyncContentFactory** и **GitSyncEntuziastov75Vps**.

3. **Ручной пуш** после правок:
   - content-factory: `git-entuziastov.ps1 -project factory -type feat -message "описание"`
   - тема/VPS: `deploy-theme-then-git.ps1` (деплой + коммит + пуш) или `git-entuziastov.ps1 -project vps`

---

## 4. Сводка

| Папка | Push в main | Cron (Actions) | Локальная задача (30 мин) |
|-------|-------------|---------------|---------------------------|
| content-factory | CI (check) | каждые 6 ч | GitSyncContentFactory |
| entuziastov75-vps | Deploy to VPS | — | GitSyncEntuziastov75Vps |
