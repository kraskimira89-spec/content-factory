"""
Клиент Google Sheets API для content-factory.

Чтение Queue (задачи со статусом queue), Services (данные услуг).
Запись обратно: wp_page_id, wp_url, status=done.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Корень проекта
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "config" / "shared-config.json"


def _load_config() -> dict:
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _get_sheets_service():
    """Возвращает объект Sheets API service (lazy, с проверкой credentials)."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        p = Path(creds_path)
        if not p.is_absolute():
            p = _PROJECT_ROOT / p
        if p.is_file():
            creds_path = str(p)
    if not creds_path or not Path(creds_path).is_file():
        creds_path = str(_PROJECT_ROOT / "config" / "google_service_account.json")
    if not Path(creds_path).is_file():
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS не задан или файл не найден. "
            "Создайте сервисный аккаунт в GCP, скачайте JSON в config/google_service_account.json"
        )
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(creds_path)
    return build("sheets", "v4", credentials=creds)


def _rows_to_dicts(sheet_name: str, rows: list[list], headers: list[str]) -> list[dict]:
    """Преобразует строки в список словарей по заголовкам."""
    if not rows:
        return []
    # Первая строка — заголовки (или используем переданные)
    if not headers:
        headers = [str(h).strip() for h in (rows[0] if rows else [])]
        data_rows = rows[1:]
    else:
        data_rows = rows

    result = []
    for row in data_rows:
        rec = {}
        for i, h in enumerate(headers):
            if i < len(row):
                rec[h] = row[i]
            else:
                rec[h] = ""
        result.append(rec)
    return result


def get_queue_tasks(status_filter: str = "queue") -> list[dict[str, Any]]:
    """
    Читает лист Queue, возвращает задачи с status=status_filter.
    Каждая задача: {id, slug, status, planned_date, topic_id, _row} (индекс строки 1-based).
    """
    config = _load_config()
    gs = config.get("google_sheets", {})
    spreadsheet_id = gs.get("spreadsheet_id")
    if not spreadsheet_id:
        raise RuntimeError("google_sheets.spreadsheet_id не задан в shared-config.json")

    service = _get_sheets_service()
    sheet_config = gs.get("sheets", {}).get("Queue", {})
    range_name = f"Queue!{sheet_config.get('range', 'A:I')}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []

    headers_raw = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    header_map = {
        "queue_id": "id", "id": "id", "task_id": "id",
        "slug": "slug", "service_slug": "slug",
        "status": "status", "state": "status",
        "planned_date": "planned_date", "publish_date": "planned_date", "date": "planned_date",
        "topic_id": "topic_id", "topic": "topic_id",
    }
    headers = [header_map.get(h, h) for h in headers_raw]

    tasks = []
    for i, row in enumerate(rows[1:], start=2):
        rec = {}
        for j, h in enumerate(headers):
            val = row[j] if j < len(row) else ""
            rec[h] = str(val).strip() if val else ""
        if rec.get("status", "").lower() == status_filter.lower():
            rec["_row"] = i
            tasks.append(rec)
    return tasks


def update_queue_status(row_index: int, status: str = "done") -> None:
    """Обновляет статус задачи в строке row_index (1-based)."""
    config = _load_config()
    spreadsheet_id = config.get("google_sheets", {}).get("spreadsheet_id")
    if not spreadsheet_id:
        raise RuntimeError("google_sheets.spreadsheet_id не задан")

    service = _get_sheets_service()
    # status в колонке E (A=queue_id, B=topic_id, C=service_slug, D=publish_date, E=status, F=wp_page_id, G=wp_url)
    range_name = f"Queue!E{row_index}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [[status]]},
    ).execute()


def get_services() -> list[dict[str, Any]]:
    """Читает лист Services. Возвращает [{slug, wp_page_id, category, price, wp_url, name, _row}, ...]."""
    config = _load_config()
    gs = config.get("google_sheets", {})
    spreadsheet_id = gs.get("spreadsheet_id")
    if not spreadsheet_id:
        raise RuntimeError("google_sheets.spreadsheet_id не задан")

    service = _get_sheets_service()
    range_name = "Services!A:F"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []

    headers_raw = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    header_map = {
        "slug": "slug", "service_slug": "slug",
        "wp_page_id": "wp_page_id", "category": "category",
        "price": "price", "wp_url": "wp_url", "name": "name",
    }
    headers = [header_map.get(h, h) for h in headers_raw]

    services = []
    for i, row in enumerate(rows[1:], start=2):
        rec = {}
        for j, h in enumerate(headers):
            val = row[j] if j < len(row) else ""
            rec[h] = str(val).strip() if val else ""
        rec["_row"] = i
        services.append(rec)
    return services


def update_service_wp_data(slug: str, wp_page_id: int | str, wp_url: str) -> None:
    """
    Обновляет wp_page_id и wp_url для услуги с заданным slug.
    Ищет строку по slug в колонке A, обновляет B (wp_page_id) и E (wp_url) отдельно.
    """
    services = get_services()
    for s in services:
        if s.get("slug", "").strip().lower() == slug.strip().lower():
            row = s["_row"]
            break
    else:
        raise ValueError(f"Услуга со slug «{slug}» не найдена в листе Services")

    config = _load_config()
    spreadsheet_id = config.get("google_sheets", {}).get("spreadsheet_id")
    service = _get_sheets_service()
    for col, val in [("B", str(wp_page_id)), ("E", wp_url)]:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Services!{col}{row}",
            valueInputOption="RAW",
            body={"values": [[val]]},
        ).execute()


def _find_queue_row_by_slug(slug: str) -> int | None:
    """Возвращает номер строки (1-based) в Queue для service_slug или None."""
    config = _load_config()
    service = _get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=config["google_sheets"]["spreadsheet_id"],
        range="Queue!A:I",
    ).execute()
    rows = result.get("values", [])
    # Колонка C (индекс 2) = service_slug
    for i, row in enumerate(rows[1:], start=2):
        s = row[2] if len(row) > 2 else ""
        if str(s).strip().lower() == slug.strip().lower():
            return i
    return None


def mark_queue_done_and_update_service(
    slug: str, wp_page_id: int | str, wp_url: str, queue_row_index: int | None = None
) -> None:
    """
    После публикации: обновляет Services (wp_page_id, wp_url) и Queue (status=done).
    queue_row_index — номер строки в Queue. Если None — ищем по slug.
    """
    config = _load_config()
    spreadsheet_id = config.get("google_sheets", {}).get("spreadsheet_id")
    service = _get_sheets_service()

    row = queue_row_index if queue_row_index is not None else _find_queue_row_by_slug(slug)
    if row is None:
        return
    # Queue: E=status, F=wp_page_id, G=wp_url
    for col, val in [("E", "done"), ("F", str(wp_page_id)), ("G", wp_url)]:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Queue!{col}{row}",
            valueInputOption="RAW",
            body={"values": [[val]]},
        ).execute()

    # Опционально: обновить Services, если лист есть
    try:
        services = get_services()
        for s in services:
            if (s.get("slug") or s.get("service_slug") or "").strip().lower() == slug.strip().lower():
                for col, val in [("B", str(wp_page_id)), ("E", wp_url)]:
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=f"Services!{col}{s['_row']}",
                        valueInputOption="RAW",
                        body={"values": [[val]]},
                    ).execute()
                break
    except Exception:
        pass
