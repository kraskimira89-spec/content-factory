"""
Извлекает текст из PDF в output/aroma и сохраняет в .txt с UTF-8.

Читаемые копии: 00852_1.pdf -> 00852_1.txt (UTF-8)

Запуск: python scripts/pdf_to_readable_txt.py
        python scripts/pdf_to_readable_txt.py output/aroma/00852_1.pdf ...
"""
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AROMA_DIR = PROJECT_ROOT / "output" / "aroma"


def extract_and_save(pdf_path: Path) -> bool:
    try:
        doc = fitz.open(pdf_path)
        chunks = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                chunks.append(text.strip())
        doc.close()
        if not chunks:
            return False
        content = "\n\n".join(chunks)
        txt_path = pdf_path.with_suffix(".txt")
        txt_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def main():
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        files = list(AROMA_DIR.glob("*.pdf"))

    for pdf_path in sorted(files):
        if not pdf_path.exists():
            continue
        ok = extract_and_save(pdf_path)
        status = "[OK]" if ok else "[fail]"
        print(f"  {status} {pdf_path.name}")

    print("\nГотово. Текст в .txt (UTF-8).")


if __name__ == "__main__":
    main()
