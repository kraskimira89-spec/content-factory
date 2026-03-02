#!/usr/bin/env python3
"""Быстрый тест config_loader: пути и блок image_protocol."""
import sys
from pathlib import Path

# Запуск из корня проекта
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import get_image_protocol, get_image_storage_root, load_shared_config

def main():
    config = load_shared_config()
    print("load_shared_config(): ключи верхнего уровня:", list(config.keys())[:8], "...")

    proto = get_image_protocol(config)
    print("get_image_protocol():", list(proto.keys()))
    print("  count:", proto.get("count"))
    print("  relative_path_pattern:", proto.get("relative_path_pattern"))

    root = get_image_storage_root()
    print("get_image_storage_root():", root)
    print("  exists:", root.exists())
    print("  absolute:", root.resolve())

if __name__ == "__main__":
    main()
