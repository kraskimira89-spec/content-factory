# Обновление PHP до 8.3 на Ubuntu (VPS reg.ru)

Инструкция для переключения сайта WordPress с PHP 8.1 на PHP 8.3. Выполнять по SSH (в т.ч. из Cursor: Terminal → подключиться к серверу).

---

## 1. Подключение и проверка текущей схемы

```bash
ssh root@91.229.11.147
# или ваш пользователь и хост

php -v
# Текущая версия (например 8.1.2)

# Какой веб-сервер
systemctl is-active nginx apache2 2>/dev/null
# Две строки: nginx — inactive/active, apache2 — inactive/active

# Есть ли PHP-FPM (сокеты)?
ls /run/php/ 2>/dev/null
```

**Как понять схему:**

- **Apache active** и **каталога `/run/php/` нет** → используется **Apache + mod_php** (модуль PHP внутри Apache). Переходите к разделу 3 (Apache + mod_php).
- **Nginx active** или **есть `/run/php/php*-fpm.sock`** → используется **PHP-FPM**. Переходите к разделу 4 или 5.

---

## 2. PPA для Ubuntu 22.04 (обязательно)

В стандартных репозиториях Ubuntu 22.04 (Jammy) есть только PHP 8.1. Пакеты PHP 8.3 даёт PPA Ondřej Surý:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:ondrej/php
# На запрос нажмите Enter
sudo apt update
```

После этого станут доступны пакеты `php8.3`, `libapache2-mod-php8.3` и т.д.

---

## 3. Вариант A: Apache + mod_php (без FPM)

Если у вас **Apache** и **нет каталога `/run/php/`** — PHP работает как модуль Apache. Установка и переключение:

```bash
# После добавления PPA (раздел 2)
sudo apt install -y php8.3 php8.3-cli php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring
# Пакет libapache2-mod-php8.3 установится зависимостью; при установке модуль php8.3 обычно включается автоматически

# Если модуль php8.1 ещё включён — отключить
sudo a2dismod php8.1

# Включить модуль php8.3 (если не включился при установке)
sudo a2enmod php8.3

# Перезапустить Apache
sudo systemctl restart apache2
```

CLI (по желанию):

```bash
sudo update-alternatives --set php /usr/bin/php8.3
php -v
```

Правки конфигов и сокетов FPM не нужны. Проверка — раздел 6.

---

## 4. Переключение версии по умолчанию для CLI

Для консоли (cron, WP-CLI, скрипты) — если ещё не сделали в разделе 3:

```bash
sudo update-alternatives --config php
# Выбрать номер строки с php8.3
```

Или одной командой:

```bash
sudo update-alternatives --set php /usr/bin/php8.3
php -v
# Должно быть PHP 8.3.x
```

---

## 5. Вариант B: Переключение веб-сайта на PHP 8.3 (Nginx + PHP-FPM)

Сайт в браузере работает через веб-сервер и **PHP-FPM**. Сначала установите (после PPA, раздел 2):

```bash
sudo apt install -y php8.3 php8.3-cli php8.3-fpm php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring
```

Далее — указать в конфиге Nginx сокет `php8.3-fpm`.

### 5.1. Найти конфиг сайта

```bash
sudo grep -R "php.*fpm.sock" /etc/nginx/
# Обычно: /etc/nginx/sites-available/ или /etc/nginx/conf.d/
```

### 4.2. Отредактировать конфиг

В блоке `location ~ \.php$` заменить путь сокета:

```nginx
# Было (пример):
fastcgi_pass unix:/run/php/php8.1-fpm.sock;

# Стало:
fastcgi_pass unix:/run/php/php8.3-fpm.sock;
```

Файл править, например:

```bash
sudo nano /etc/nginx/sites-available/ваш-сайт
# или
sudo nano /etc/nginx/conf.d/wordpress.conf
```

### 5.3. Проверить конфиг и перезапустить

```bash
sudo nginx -t
sudo systemctl restart php8.3-fpm
sudo systemctl reload nginx
```

---

## 6. Вариант C: Переключение веб-сайта (Apache + PHP-FPM)

Если используется Apache с FPM (есть `/run/php/php*-fpm.sock`), установите `php8.3-fpm` (после PPA), в конфиге виртуального хоста замените путь сокета на `php8.3-fpm.sock` и перезапустите:

```bash
sudo systemctl restart php8.3-fpm
sudo systemctl reload apache2
```

---

## 7. Проверка

- В браузере: открыть сайт и админку WordPress.
- В консоли: `php -v` → 8.3.x.
- В WordPress: «Инструменты → Здоровье сайта» — предупреждение о версии PHP должно исчезнуть.

---

## 8. Отключение старого PHP (после успешной проверки)

**Только если использовался PHP-FPM** (варианты B или C):

```bash
sudo systemctl stop php8.1-fpm
sudo systemctl disable php8.1-fpm
```

Для варианта A (Apache + mod_php) модуль php8.1 уже отключён через `a2dismod`.

Пакеты PHP 8.1 можно оставить или удалить:

```bash
# опционально
sudo apt remove --purge php8.1 php8.1-*
```

---

## Выполнение через Cursor

1. **Terminal → New Terminal.**
2. Подключиться к серверу: `ssh root@91.229.11.147`.
3. **Все команды с `sudo` выполняйте только в сессии SSH** (на сервере). В локальной PowerShell (Windows) `sudo` и `systemctl` не работают — после обрыва SSH переподключитесь и продолжайте на сервере.
4. Выполнять команды по порядку: раздел 2 (PPA), затем раздел 3 (Apache + mod_php) или 5–6 (Nginx/Apache + FPM).
5. Либо скопировать на сервер и запустить скрипт: `scripts/upgrade-php-8.3-ubuntu.sh` (см. комментарии в скрипте — часть шагов может потребовать ручного редактирования конфига Nginx/Apache).
