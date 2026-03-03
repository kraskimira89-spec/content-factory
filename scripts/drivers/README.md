# Драйверы для парсера Gloryon

## YandexDriver

Для полного парсинга с Yandex Browser используй **YandexDriver** вместо ChromeDriver.

1. Скачай `yandexdriver.exe` с [GitHub Releases](https://github.com/yandex/YandexDriver/releases)
2. Выбери версию, совпадающую с мажорной версией Yandex Browser (например, 25.x для Yandex 25.8)
3. Положи `yandexdriver.exe` в эту папку: `scripts/drivers/`

Альтернатива: укажи путь в `config/.env`:
```
YANDEX_DRIVER_PATH=D:\путь\к\yandexdriver.exe
```
