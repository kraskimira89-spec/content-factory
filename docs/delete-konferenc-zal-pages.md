# Удаление страниц конференц-зала

Страницы `konferenc-zal`, `korporativnye-treningi`, `onlajn-shkoly`, `kouchting` (включая дочерние под родителем) можно удалить через скрипт `scripts/delete_konferenc_zal_pages.py`. Он использует WP REST API и учётные данные из `config/.env` (WP_URL, WP_USERNAME, WP_APP_PASSWORD).

**Рекомендуемый порядок:** сначала запустите с `--dry-run`, чтобы увидеть, какие страницы будут удалены, затем без флага — для фактического удаления (страницы попадут в корзину WordPress).

```bash
python scripts/delete_konferenc_zal_pages.py --dry-run
python scripts/delete_konferenc_zal_pages.py
```
