# Автоматический деплой темы на VPS

Способы автоматически выполнять `python scripts/deploy_to_vps.py --mode theme`.

---

## 1. Планировщик заданий Windows

Деплой по расписанию (например, ежедневно в 09:00).

### Однократный деплой без git

```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-only.ps1"
```

### Регистрация задачи в Планировщике (один раз)

```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\register-deploy-task.ps1"
```

- По умолчанию задача **DeployThemeToVPS** запускается **ежедневно в 09:00**.
- Варианты расписания: `-Schedule daily` (по умолчанию), `-Schedule hourly`, `-Schedule atlogon`.

Проверка: **Планировщик заданий** (taskschd.msc) → Библиотека → DeployThemeToVPS.

---

## 2. Git hook (деплой после каждого коммита в репо темы)

В репозитории темы **seo_entuziastov75** после каждого `git commit` автоматически выполняется деплой.

### Установка (один раз)

Из корня репозитория темы (например, `C:\Users\user\Documents\seo_entuziastov75`):

```powershell
powershell -ExecutionPolicy Bypass -File "scripts\install-deploy-hook.ps1"
```

Хук копируется в `.git/hooks/post-commit`. При необходимости в Git Bash выполните:

```bash
chmod +x .git/hooks/post-commit
```

---

## 3. Деплой + коммит и пуш (вручную или по задаче)

Полный цикл: деплой на VPS → коммит в репо темы → пуш в GitHub:

```powershell
powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-then-git.ps1" -type feat -message "описание изменений"
```

---

## Пути

- **content-factory:** `D:\content-factory`
- **Репо темы (vps):** `C:\Users\user\Documents\seo_entuziastov75` или `D:\entuziastov75-vps`

В хуке и задаче используется путь к content-factory для вызова `deploy_to_vps.py`. Если у вас другой диск/путь, отредактируйте `scripts/deploy-theme-only.ps1`, `scripts/register-deploy-task.ps1` и `seo_entuziastov75/scripts/git-hooks/post-commit`.
