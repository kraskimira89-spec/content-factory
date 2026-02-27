# -*- coding: utf-8 -*-
"""Строит дерево папок и сохраняет в docs/project-tree.txt (без venv)."""
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
EXCLUDE = {'venv', '.git'}
OUTPUT = os.path.join(ROOT, 'docs', 'project-tree.txt')


def tree_lines(dirpath, prefix='', is_last=True):
    try:
        names = sorted(os.listdir(dirpath))
    except PermissionError:
        return []
    names = [n for n in names if n not in EXCLUDE]
    dirs = [n for n in names if os.path.isdir(os.path.join(dirpath, n))]
    files = [n for n in names if os.path.isfile(os.path.join(dirpath, n))]
    entries = dirs + files
    lines = []
    for i, name in enumerate(entries):
        last = (i == len(entries) - 1)
        connector = '\u2514\u2500\u2500 ' if last else '\u251c\u2500\u2500 '
        lines.append(prefix + connector + name)
        if name in dirs:
            ext = '    ' if last else '\u2502   '
            subpath = os.path.join(dirpath, name)
            if not subpath.startswith(ROOT):
                continue
            rel = os.path.relpath(subpath, ROOT)
            if rel.startswith('venv') or os.sep + 'venv' + os.sep in rel:
                continue
            lines.extend(tree_lines(subpath, prefix + ext, last))
    return lines


def main():
    root_name = os.path.basename(ROOT) or 'content-factory'
    lines = [root_name + '/'] + tree_lines(ROOT)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('Saved:', OUTPUT)


if __name__ == '__main__':
    main()
