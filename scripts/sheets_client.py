import os
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

CREDENTIALS_FILE = Path(os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(Path(__file__).resolve().parent.parent / "config" / "google_service_account.json")
))

def get_sheets_service():
    creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_queue(spreadsheet_id: str, status_filter: str | None = "queue"):
    """Читает Queue. status_filter=None — все строки, иначе только с этим статусом."""
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Queue!A:I"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    data = [dict(zip(headers, row)) for row in rows[1:]]
    if status_filter is None:
        return data
    return [r for r in data if (r.get("status") or "").strip().lower() == str(status_filter).strip().lower()]


def update_queue_row(spreadsheet_id: str, row_number: int, updates: dict):
    service = get_sheets_service()
    for col, value in updates.items():
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Queue!{col}{row_number}",
            valueInputOption="RAW",
            body={"values": [[value]]}
        ).execute()


def write_sheet_range(spreadsheet_id: str, range_name: str, values: list[list]) -> None:
    """Записывает values в указанный range (например, Services!A1:F10)."""
    service = get_sheets_service()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


if __name__ == "__main__":
    rows = read_queue("1uL2BUXrN-E85s3OEz9DjzeT8rQouBpTQZOMjwUEmquo", "queue")
    print(f"Найдено строк со статусом queue: {len(rows)}")
    for r in rows:
        print(r)
