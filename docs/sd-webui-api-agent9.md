# SD WebUI: API для agent9 и отключение facechain

Чтобы agent9 успешно вызывал генерацию картинок, нужен доступ к API SD WebUI. Ошибки расширения facechain в логе на это не влияют, но мешают читать вывод.

## 1. Включить API в webui-user.bat

В папке SD WebUI (например `D:\AI\stable-diffusion-webui`) открой **webui-user.bat** и убедись, что есть:

```bat
set PYTHON=
set GIT=
set VENV_DIR=
set COMMANDLINE_ARGS=--api
```

Главное — **`--api`**: тогда станет доступен `/sdapi/v1/txt2img` для agent9.

## 2. Убрать ошибки facechain из лога

Расширение facechain при загрузке тянет зависимости (mmcv, mediapipe) и засоряет лог. Для задачи agent9 оно не нужно.

- В папке `D:\AI\stable-diffusion-webui\extensions` папка `facechain` переименована в `_facechain_disabled` (уже сделано). Если вернёшь имя `facechain`, снова переименуй в `_facechain_disabled` или удали.
- Перезапусти **webui-user.bat** (или `webui.bat --api`). SD WebUI поднимется без попыток ставить зависимости facechain.

## 3. Проверка после перезапуска

1. Открой в браузере: **http://127.0.0.1:7860** — должна открыться SD WebUI.
2. Открой **http://127.0.0.1:7860/docs** — должна открыться Swagger-страница API. Если она есть, API включён.
3. В `config/.env` должен быть порт, на котором реально запустился WebUI (если не 7860, то 7861, 7862…):
   ```env
   SD_WEBUI_URL=http://127.0.0.1:7860
   ```

## 4. Запуск agent9

Из корня проекта:

```cmd
cd D:\content-factory
python seo-agents\agent9_images_runner.py --plan-json output\20260304_135503_page_Ароматерапия_Ноябрьск.images-plan.json --output-json output\20260304_135503_page_Ароматерапия_Ноябрьск.images-generated.json --slug aromaterapiya
```

## Что проверить и написать после шагов 2–4

1. **Открывается ли http://127.0.0.1:7860/docs** после переименования/отключения facechain и перезапуска SD?
2. **Что показывает лог agent9 при старте первой картинки** — есть ли запрос к `/sdapi/v1/txt2img`, успешный ответ (без 404 и connection refused)?

После успешного прогона agent9 запусти agent4 для обновления страницы в WordPress:

```cmd
python seo-agents\agent4_publish\agent_4_publish.py aromaterapiya
```
