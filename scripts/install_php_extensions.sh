#!/bin/bash
echo "=== PHP version ==="
php -v 2>/dev/null || true
PHP_VER=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;" 2>/dev/null | tr -d '\n\r')
[ -z "$PHP_VER" ] && PHP_VER=8.1
echo "PHP version: $PHP_VER"
echo "=== Installing imagick and intl ==="
sudo apt-get update -qq
sudo apt-get install -y php"$PHP_VER"-imagick php"$PHP_VER"-intl
echo "=== Restarting PHP-FPM ==="
sudo systemctl restart php"$PHP_VER"-fpm 2>/dev/null || sudo systemctl restart php-fpm 2>/dev/null || sudo systemctl restart apache2 2>/dev/null || true
echo "=== Verifying ==="
php -m | grep -E "imagick|intl" || echo "Check: php -m"
