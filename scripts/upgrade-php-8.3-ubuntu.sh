#!/bin/bash
# Обновление PHP до 8.3 на Ubuntu (VPS reg.ru / WordPress).
# Запускать на сервере по SSH (можно из Cursor: ssh user@host, затем bash upgrade-php-8.3-ubuntu.sh).
# Часть шагов (правка конфига Nginx/Apache) может потребовать ручного редактирования.

set -e

echo "=== 1. Текущая версия PHP и веб-сервер ==="
php -v 2>/dev/null || true
systemctl is-active nginx 2>/dev/null && echo "Nginx: active" || true
systemctl is-active apache2 2>/dev/null && echo "Apache: active" || true
ls -la /run/php/*.sock 2>/dev/null || true

echo ""
echo "=== 2. Установка PHP 8.3 (пакеты reg.ru) ==="
sudo apt update
sudo apt install -y php8.3 php8.3-cli php8.3-fpm php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring \
  php8.3-gd php8.3-zip php8.3-intl php8.3-bcmath 2>/dev/null || \
sudo apt install -y php8.3 php8.3-cli php8.3-fpm php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring

echo ""
echo "=== 3. Переключение CLI на PHP 8.3 ==="
if [ -x /usr/bin/php8.3 ]; then
  sudo update-alternatives --set php /usr/bin/php8.3 2>/dev/null || sudo update-alternatives --config php
  php -v
else
  echo "PHP 8.3 не найден, проверьте установку."
  exit 1
fi

echo ""
echo "=== 4. Проверка сокета PHP 8.3 FPM ==="
if [ -S /run/php/php8.3-fpm.sock ]; then
  echo "Сокет php8.3-fpm.sock найден."
else
  sudo systemctl start php8.3-fpm
  echo "Запущен php8.3-fpm."
fi

echo ""
echo "=== 5. Конфиг веб-сервера (требуется ручная правка) ==="
echo "Найдите конфиг, где указан php*-fpm.sock:"
sudo grep -l "php.*fpm.sock" /etc/nginx/sites-enabled/* /etc/nginx/conf.d/* 2>/dev/null || true
sudo grep -l "php.*fpm.sock" /etc/apache2/sites-enabled/* 2>/dev/null || true
echo ""
echo "Замените в конфиге: php8.1-fpm.sock → php8.3-fpm.sock"
echo "Пример для Nginx: fastcgi_pass unix:/run/php/php8.3-fpm.sock;"
echo "После правки выполните вручную:"
echo "  sudo nginx -t && sudo systemctl restart php8.3-fpm && sudo systemctl reload nginx"
echo "  или для Apache: sudo systemctl restart php8.3-fpm && sudo systemctl reload apache2"
echo ""
read -p "Уже заменили сокет в конфиге и перезапустили веб-сервер? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Выполните шаг 5 вручную, затем перезапустите FPM и веб-сервер."
  exit 0
fi

echo ""
echo "=== 6. Перезапуск PHP 8.3 FPM ==="
sudo systemctl restart php8.3-fpm
if systemctl is-active nginx &>/dev/null; then
  sudo systemctl reload nginx
elif systemctl is-active apache2 &>/dev/null; then
  sudo systemctl reload apache2
fi

echo ""
echo "=== Готово. Проверьте сайт в браузере и «Здоровье сайта» в WordPress. ==="
echo "Чтобы отключить старый PHP 8.1 FPM: sudo systemctl stop php8.1-fpm && sudo systemctl disable php8.1-fpm"
