# Конференц-зал — макет Figma Make

## Ссылки на макет

- [Figma Make — лендинг конференц-зала](https://www.figma.com/make/pBV4BexEWro19a4LkHEki6/%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D1%82%D1%8C-%D0%BB%D0%B5%D0%BD%D0%B4%D0%B8%D0%BD%D0%B3-%D0%BA%D0%BE%D0%BD%D1%84%D0%B5%D1%80%D0%B5%D0%BD%D1%86-%D0%B7%D0%B0%D0%BB%D0%B0?p=f&t=kgXxvCxf1CADkkU4-0)
- [Тот же файл, вид 2](https://www.figma.com/make/pBV4BexEWro19a4LkHEki6/%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D1%82%D1%8C-%D0%BB%D0%B5%D0%BD%D0%B4%D0%B8%D0%BD%D0%B3-%D0%BA%D0%BE%D0%BD%D1%84%D0%B5%D1%80%D0%B5%D0%BD%D1%86-%D0%B7%D0%B0%D0%BB%D0%B0?t=kgXxvCxf1CADkkU4-1)

В ссылках Figma Make нет параметра `node-id` (есть только `t=...`). Для реализации использован визуальный макет: порядок секций, тексты, две акцентные кнопки (бирюза + коралл).

## «Живая» спецификация (React)

В папке **`design/Design-main`** — экспорт из Figma Make: Vite + React + Tailwind, полный лендинг конференц-зала. Используйте как эталон при правках темы WordPress.

**Запуск:**
```bash
cd design/Design-main
npm install
npm run dev
```
Открыть в браузере: **http://localhost:5173/**

Компоненты: `Hero`, `EventTypes`, `Equipment`, `Gallery`, `Pricing`, `AdditionalServices`, `BookingForm`, `FAQ`, `Testimonials`, `Footer` — соответствуют секциям в `template-page-landing-konferenc-zal.php`.

## Реализация в коде (WordPress)

- Шаблон: `entuziastov75-child` → `template-page-landing-konferenc-zal.php`
- Стили: `assets/css/landing-pages.css`
- Данные: заголовок/контент страницы, `get_theme_mod( 'konferenc_zal_rate_per_hour', 1500 )`, контакты из темы.
