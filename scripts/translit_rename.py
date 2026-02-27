# -*- coding: utf-8 -*-
"""
Переименование файлов и папок: русские названия -> латиница (транслитерация).
Запуск из корня проекта: python scripts/translit_rename.py
"""
import os
import sys

# ГОСТ 7.79-2000 (Б) — транслитерация кириллицы в латиницу
TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z',
    'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z',
    'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
}
# Символы, которые в именах файлов заменяем на подчёркивание
REPLACE_CHARS = ' <>«»"\'\\/:|?*'


def has_cyrillic(s):
    return any('\u0400' <= c <= '\u04FF' for c in s)


def translit_name(name):
    result = []
    for c in name:
        if c in TRANSLIT:
            result.append(TRANSLIT[c])
        elif c in REPLACE_CHARS:
            result.append('_' if c == ' ' else '_')
        else:
            result.append(c)
    s = ''.join(result)
    while '__' in s:
        s = s.replace('__', '_')
    return s.strip('_') or name


def main():
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    if not os.path.isdir(root):
        print('Корень проекта не найден:', root)
        sys.exit(1)
    exclude = {'venv', '.git'}
    # Собираем все пути (сначала файлы, потом папки), у которых в имени есть кириллица
    to_rename = []  # (full_path, new_basename)
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir.startswith('venv') or 'venv' in rel_dir.split(os.sep):
            continue
        for name in filenames:
            if has_cyrillic(name):
                new_name = translit_name(name)
                if new_name != name:
                    full = os.path.join(dirpath, name)
                    to_rename.append((full, os.path.join(dirpath, new_name)))
        for name in dirnames:
            if has_cyrillic(name):
                new_name = translit_name(name)
                if new_name != name:
                    full = os.path.join(dirpath, name)
                    to_rename.append((full, os.path.join(dirpath, new_name)))
    # Сортируем по длине пути по убыванию — сначала переименовываем самые вложенные
    to_rename.sort(key=lambda x: len(x[0]), reverse=True)
    for old_path, new_path in to_rename:
        if not os.path.exists(old_path):
            continue
        if os.path.exists(new_path):
            print('Пропуск (уже есть):', new_path)
            continue
        try:
            os.rename(old_path, new_path)
            print('OK:', os.path.basename(old_path), '->', os.path.basename(new_path))
        except Exception as e:
            print('Ошибка:', old_path, e)
    print('Готово. Переименовано путей:', len(to_rename))


if __name__ == '__main__':
    main()
