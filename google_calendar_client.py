import os
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.httplib2 import Request as HttplibRequest
import google.auth.httplib2
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json
import pickle
import httplib2

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    """Get or create a Google Calendar service with cached token."""
    creds = None
    token_file = ".google_calendar_token.pickle"

    # Try to load cached token
    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    # If no cached token, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
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

    return build("calendar", "v3", credentials=creds)

def read_calendar_busy_blocks(date_str=None):
    """Read all busy blocks from the configured calendar for a given date (default today)."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    service = get_calendar_service()
    cal_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not cal_id:
        raise ValueError("GOOGLE_CALENDAR_ID not set in .env")

    start_of_day = f"{date_str}T00:00:00"
    end_of_day = f"{date_str}T23:59:59"

    events = service.events().list(
        calendarId=cal_id,
        timeMin=start_of_day + "Z",
        timeMax=end_of_day + "Z",
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    busy_blocks = []
    for event in events.get("items", []):
        start = event["start"]["dateTime"] if "dateTime" in event["start"] else None
        end = event["end"]["dateTime"] if "dateTime" in event["end"] else None
        if start and end:
            busy_blocks.append({
                "start": start,
                "end": end,
                "summary": event.get("summary", "Busy")
            })

    return busy_blocks

def write_calendar_event(task_id, task_title, start_time, end_time, context, idempotency_key):
    """Write an event to the calendar. Returns the event ID."""
    service = get_calendar_service()
    cal_id = os.getenv("GOOGLE_CALENDAR_ID")

    event = {
        "summary": task_title,
        "description": f"Task ID: {task_id}\nContext: {context}\nIdempotency Key: {idempotency_key}",
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }

    result = service.events().insert(calendarId=cal_id, body=event).execute()
    return result["id"]

def simulate_failure():
    """Raise an exception to simulate a Calendar API failure (for demo/testing)."""
    raise Exception("Simulated Calendar API failure")
