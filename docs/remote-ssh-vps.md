# Remote-SSH: подключение к VPS

Работа с проектом entuziastov75-vps через Cursor / VS Code.

---

## 1. Подготовка

### Проверь наличие SSH-ключа

```powershell
# Список ключей
Get-ChildItem $env:USERPROFILE\.ssh

# Должен быть id_rsa (приватный) и id_rsa.pub (публичный)
# Если нет — создай: ssh-keygen -t rsa -b 4096
```

### Добавь ключ на VPS (если ещё не добавлен)

```powershell
# Скопировать публичный ключ на сервер
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh root@91.229.11.147 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Или вручную: скопировать содержимое `id_rsa.pub` и добавить в `/root/.ssh/authorized_keys` на сервере.

### Проверь подключение

```powershell
ssh root@91.229.11.147
# Должно подключиться без пароля (по ключу)
```

---

## 2. Настройка Remote-SSH в Cursor

### Вариант А: через командную палитру

1. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host…**
2. Выбери **Configure SSH Hosts…** или введи хост вручную
3. Укажи хост (см. ниже)

### Вариант Б: через SSH config

Открой `C:\Users\<user>\.ssh\config` и добавь:

```
Host entuziastov75-vps
    HostName 91.229.11.147
    User root
    IdentityFile ~/.ssh/id_rsa
```

Сохрани. Тогда в Cursor при **Connect to Host** появится пункт `entuziastov75-vps`.

---

## 3. Подключение к проекту

1. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host…**
2. Выбери `root@91.229.11.147` или `entuziastov75-vps`
3. Откроется новое окно Cursor, подключённое к серверу
4. **File → Open Folder…**
5. Укажи путь: **`/root/sites/entuziastov75VPS`**

---

## 4. Структура проекта на VPS

```
/root/sites/entuziastov75VPS/
├── shared-config.json
├── www/
│   └── entuziastov75.ru/          ← WordPress
│       └── wp-content/
│           └── themes/
│               └── flavor/        ← тема, шаблоны страниц услуг
├── docs/
├── prompts/
└── scripts/
```

Шаблоны страниц услуг — в `www/entuziastov75.ru/wp-content/themes/flavor/`.

---

## 5. Multi-root: content-factory + VPS

Чтобы иметь оба проекта в одном окне:

1. Подключись по Remote-SSH к VPS и открой `/root/sites/entuziastov75VPS`
2. **File → Add Folder to Workspace…**
3. Укажи локальную папку: `D:\content-factory`  
   (Cursor подключит её из локальной системы)
4. **File → Save Workspace As…** → `content-and-vps-remote.code-workspace`

В результате: content-factory локально, entuziastov75-vps по SSH в одном workspace.

---

## 6. Переменные из config/.env

Для деплоя используются (можно сверить с `.env`):

| Переменная  | Пример            |
|-------------|-------------------|
| VPS_HOST    | 91.229.11.147     |
| VPS_USER    | root              |
| VPS_SSH_KEY | ~/.ssh/id_rsa     |

---

## 7. Быстрая команда

```powershell
# Подключение по SSH в терминале
ssh root@91.229.11.147 -i $env:USERPROFILE\.ssh\id_rsa
```

---

## 8. Обновление PHP на VPS

Если WordPress показывает предупреждение о старой версии PHP (8.1) и рекомендует 8.3:

- **Инструкция:** [docs/php-upgrade-ubuntu-regru.md](php-upgrade-ubuntu-regru.md) — установка PHP 8.3, переключение CLI и веб-сервера (Nginx/Apache + FPM).
- **Скрипт:** `scripts/upgrade-php-8.3-ubuntu.sh` — можно скопировать на сервер и запустить по SSH; правку конфига сокета FPM нужно сделать вручную.
