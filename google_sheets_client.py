import os
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
import pickle

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    """Get or create a Google Sheets service with cached token."""
    creds = None
    token_file = ".google_sheets_token.pickle"

    # Try to load cached token
    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    # If no cached token, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
            if not os.path.exists(creds_path):
                raise ValueError(f"credentials.json not found at {creds_path}")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next time
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return build("sheets", "v4", credentials=creds)

def append_ledger_row(run_id, task_id, idempotency_key, calendar_event_id, status):
    """Append a row to the Ledger tab."""
    service = get_sheets_service()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID not set in .env")

    timestamp = datetime.now().isoformat()
    row = [run_id, task_id, idempotency_key, calendar_event_id or "", status, timestamp]

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Ledger!A:F",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

def read_ledger():
    """Read all rows from the Ledger tab."""
    service = get_sheets_service()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="Ledger!A:F"
    ).execute()

    rows = result.get("values", [])[1:]  # Skip header
    ledger = []
    for row in rows:
        if len(row) >= 6:
            ledger.append({
                "run_id": row[0],
                "task_id": row[1],
                "idempotency_key": row[2],
                "calendar_event_id": row[3],
                "status": row[4],
                "timestamp": row[5]
            })

    return ledger

def append_evaluation_row(scenario, result, metric_name, metric_value):
    """Append a row to the Evaluation tab."""
    service = get_sheets_service()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    row = [scenario, result, metric_name, metric_value]

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Evaluation!A:D",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

def clear_evaluation_tab():
    """Clear the Evaluation tab (for testing scenarios)."""
    service = get_sheets_service()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range="Evaluation!A2:D"
    ).execute()
