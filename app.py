import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

from notion_client import read_inbox_tasks, update_task_status
from google_calendar_client import read_calendar_busy_blocks, write_calendar_event, simulate_failure
from google_sheets_client import append_ledger_row, read_ledger
from scheduler import fit_schedule, get_calendar_free_slots, calculate_total_demand_and_available_time

load_dotenv()

st.set_page_config(page_title="Tempo", layout="wide")
st.title("Tempo — Planning Support")
st.markdown("Detect when a day's demand doesn't match real capacity, and make that mismatch visible.")

# Dev toggles
col1, col2 = st.columns([4, 1])
with col1:
    pass
with col2:
    simulate_failure_toggle = st.checkbox("Simulate Calendar Failure (dev only)")

st.divider()

# Main action
if st.button("Generate & Write Plan", key="main_button", use_container_width=True):
    with st.spinner("Reading tasks and calendar..."):
        try:
            # Read data
            tasks = read_inbox_tasks()
            busy_blocks = read_calendar_busy_blocks()
            free_slots = get_calendar_free_slots(busy_blocks)

            if not tasks:
                st.warning("No tasks found in Inbox.")
                st.stop()

            # Demand vs. capacity
            total_requested, total_available = calculate_total_demand_and_available_time(tasks, free_slots)

            st.info(f"📊 Demand vs. Capacity: **{total_requested:.1f}h requested** · {total_available:.1f}h available")

            # Schedule
            scheduled, deferred = fit_schedule(tasks, free_slots)

            # Display plan
            st.subheader("Scheduled Tasks")
            if scheduled:
                for task in scheduled:
                    start = task["scheduled_start"].strftime("%H:%M")
                    end = task["scheduled_end"].strftime("%H:%M")
                    st.write(f"✅ {task['title']} ({start}–{end}, {task['estimate_min']}m estimate)")
            else:
                st.write("No tasks could be scheduled.")

            st.subheader("Deferred Tasks")
            if deferred:
                for task in deferred:
                    st.write(f"⏸ {task['title']} (deferred, {task['estimate_min']}m estimate)")
            else:
                st.write("No deferred tasks.")

            # Approval and write
            if st.button("Approve & Write to Calendar", key="approve_button"):
                with st.spinner("Writing to Calendar and Sheets..."):
                    run_id = str(uuid.uuid4())[:8]
                    success_count = 0
                    failure_count = 0

                    for task in scheduled:
                        task_id = task["id"]
                        start_iso = task["scheduled_start"].isoformat()
                        end_iso = task["scheduled_end"].isoformat()
                        idempotency_key = f"{run_id}:{task_id}:{start_iso}"

                        try:
                            # Simulate failure if toggle is on
                            if simulate_failure_toggle:
                                simulate_failure()

                            # Write to Calendar
                            event_id = write_calendar_event(
                                task_id,
                                task["title"],
                                start_iso,
                                end_iso,
                                task["context"],
                                idempotency_key
                            )

                            # Update Notion
                            update_task_status(task_id, "Planned", event_id)

                            # Log to Sheets
                            append_ledger_row(run_id, task_id, idempotency_key, event_id, "success")
                            success_count += 1

                        except Exception as e:
                            st.error(f"Failed to write {task['title']}: {str(e)}")
                            append_ledger_row(run_id, task_id, idempotency_key, "", "failed_recoverable")
                            failure_count += 1

                    for task in deferred:
                        task_id = task["id"]
                        update_task_status(task_id, "Deferred")

                    st.success(f"✅ Written: {success_count} events")
                    if failure_count > 0:
                        st.warning(f"⚠️ Failed: {failure_count} events (check Sheets Ledger for retry)")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.error("Check that .env is properly configured and credentials are valid.")

st.divider()
st.markdown("**Status:** Phase 1 - Basic scheduling loop")
