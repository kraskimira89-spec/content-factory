# Пути проектов на VPS

Справочник для Оркестратора и деплоя. Синхронизация shared-config и контракта.

---

## 1. VPS-проект (entuziastov75-vps)

**Путь на сервере:** `/root/sites/entuziastov75VPS/`  
**Репозиторий:** `kraskimira89-spec/entuziastov75-vps`

```
/root/sites/entuziastov75VPS/
├── shared-config.json          ← корень репо, контракт
├── www/entuziastov75.ru/       ← WordPress
├── docs/
├── prompts/
├── scripts/
└── ...
```

**shared-config на VPS:** `/root/sites/entuziastov75VPS/shared-config.json`

Секции контракта на VPS:
- `factory` — output_dir, agents
- `vps` — wp_url, custom_api (publish, status)
- `services` — slug → name, category, aliases
- `uslugi` — услуги под /uslugi/ (slug → name, aliases); slugs = ключи объекта
- `rubrics` — рубрики блога

---

## 2. Content-factory

**Путь на сервере:** `../content-factory` относительно VPS  
**Ожидаемый путь:** `/root/sites/content-factory/` (если лежит рядом)

**Репозиторий:** `kraskimira89-spec/content-factory`

**shared-config в content-factory:** `config/shared-config.json`

Типичная структура:

```
/root/sites/
├── entuziastov75VPS/           ← VPS
│   └── shared-config.json
└── content-factory/            ← рядом с VPS
    └── config/
        └── shared-config.json
```

---

## 3. Синхронизация shared-config

**Источник:** content-factory → `config/shared-config.json`  
**Приёмник:** entuziastov75-vps → `shared-config.json` (корень)

```bash
# На VPS, если content-factory рядом
cp /root/sites/content-factory/config/shared-config.json /root/sites/entuziastov75VPS/shared-config.json

# Или из папки entuziastov75-vps
cp ../content-factory/config/shared-config.json ./shared-config.json
```

Проверка:

```bash
diff /root/sites/content-factory/config/shared-config.json /root/sites/entuziastov75VPS/shared-config.json
```

---

## 4. Ключевые пути (content-factory, локально)

- Контракт: `config/shared-config.json`
- Ручные страницы: `materials/pages_manual/{slug}.md`
- Деплой: `scripts/deploy_to_vps.py --mode rest`
