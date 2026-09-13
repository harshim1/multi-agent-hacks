import os
from notion_client import Client
from datetime import datetime

def get_notion_client():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not set in .env")
    return Client(auth=token)

def read_inbox_tasks():
    """Read all tasks with Status = Inbox from the Notion database."""
    client = get_notion_client()
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        raise ValueError("NOTION_DATABASE_ID not set in .env")

    query = {
        "filter": {
            "property": "Status",
            "select": {"equals": "Inbox"}
        }
    }

    results = client.databases.query(db_id, **query)
    tasks = []

    for item in results.get("results", []):
        props = item["properties"]
        task = {
            "id": item["id"],
            "title": props["Title"]["title"][0]["plain_text"] if props["Title"]["title"] else "Untitled",
            "due": props["Due"]["date"]["start"] if props["Due"]["date"] else None,
            "estimate_min": props["Estimate"]["number"] if props["Estimate"]["number"] else 0,
            "context": props["Context"]["select"]["name"] if props["Context"]["select"] else "Admin",
            "priority": props["Priority"]["select"]["name"] if props["Priority"]["select"] else "Could",
            "status": props["Status"]["select"]["name"] if props["Status"]["select"] else "Inbox",
            "calendar_event_id": props["Calendar Event ID"]["rich_text"][0]["plain_text"] if props["Calendar Event ID"]["rich_text"] else None,
        }
        tasks.append(task)

    return tasks

def update_task_status(task_id, status, calendar_event_id=None):
    """Update a task's Status and optionally Calendar Event ID."""
    client = get_notion_client()
    db_id = os.getenv("NOTION_DATABASE_ID")

    update_obj = {
        "Status": {"select": {"name": status}}
    }
    if calendar_event_id:
        update_obj["Calendar Event ID"] = {"rich_text": [{"text": {"content": calendar_event_id}}]}

    client.pages.update(task_id, properties=update_obj)
