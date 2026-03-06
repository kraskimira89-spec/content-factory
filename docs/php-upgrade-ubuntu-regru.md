# Обновление PHP до 8.3 на Ubuntu (VPS reg.ru)

Инструкция для переключения сайта WordPress с PHP 8.1 на PHP 8.3. Выполнять по SSH (в т.ч. из Cursor: Terminal → подключиться к серверу).

---

## 1. Подключение и проверка текущей схемы

```bash
ssh root@91.229.11.147
# или ваш пользователь и хост

php -v
# Текущая версия (например 8.1.2)

# Какой веб-сервер и PHP-FPM
systemctl is-active nginx apache2 2>/dev/null
ls /run/php/ 2>/dev/null
# Увидите сокеты: php8.1-fpm.sock и после установки php8.3-fpm.sock
```

---

## 2. Установка PHP 8.3 (рекомендации reg.ru)

```bash
sudo apt update
sudo apt install -y php8.3 php8.3-cli php8.3-fpm php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring
```

Опционально (для WordPress/плагинов):

```bash
sudo apt install -y php8.3-gd php8.3-zip php8.3-intl php8.3-bcmath
```

---

## 3. Переключение версии по умолчанию для CLI

Для консоли (cron, WP-CLI, скрипты):

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

## 4. Переключение веб-сайта на PHP 8.3 (Nginx + PHP-FPM)

Сайт в браузере работает через веб-сервер и **PHP-FPM**. Нужно указать сокет `php8.3-fpm`.

### 4.1. Найти конфиг сайта

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

### 4.3. Проверить конфиг и перезапустить

```bash
sudo nginx -t
sudo systemctl restart php8.3-fpm
sudo systemctl reload nginx
```

---

## 5. Переключение веб-сайта (Apache + PHP-FPM)

Если используется Apache с FPM, в конфиге виртуального хоста будет путь к сокету `php8.1-fpm`. Заменить на `php8.3-fpm.sock` и перезапустить:

```bash
sudo systemctl restart php8.3-fpm
sudo systemctl reload apache2
```

---

## 6. Проверка

- В браузере: открыть сайт и админку WordPress.
- В консоли: `php -v` → 8.3.x.
- В WordPress: «Инструменты → Здоровье сайта» — предупреждение о версии PHP должно исчезнуть.

---

## 7. Отключение старого PHP-FPM (после успешной проверки)

```bash
sudo systemctl stop php8.1-fpm
sudo systemctl disable php8.1-fpm
```

Пакеты PHP 8.1 можно оставить или удалить:

```bash
# опционально
sudo apt remove --purge php8.1 php8.1-*
```

---

## Выполнение через Cursor

1. **Terminal → New Terminal.**
2. Подключиться: `ssh root@91.229.11.147`.
3. Выполнять команды из шагов 2–7 по порядку.
4. Либо скопировать на сервер и запустить скрипт: `scripts/upgrade-php-8.3-ubuntu.sh` (см. комментарии в скрипте — часть шагов может потребовать ручного редактирования конфига Nginx/Apache).
