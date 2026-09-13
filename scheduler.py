from datetime import datetime, timedelta
from typing import List, Tuple, Dict

BUFFER_MIN = 10
PRIORITY_RANK = {"Must": 0, "Should": 1, "Could": 2}

def priority_rank(priority_str):
    return PRIORITY_RANK.get(priority_str, 2)

def parse_datetime(dt_str):
    """Parse ISO datetime string."""
    if isinstance(dt_str, str):
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt_str

def get_calendar_free_slots(busy_blocks, work_start="09:00", work_end="17:00"):
    """
    Given a list of busy blocks, return a list of free slots during work hours.
    Returns list of (start, end) tuples as datetime objects.
    """
    from datetime import timezone

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Create timezone-aware work boundaries
    work_start_dt = datetime.fromisoformat(f"{today_str}T{work_start}:00+00:00")
    work_end_dt = datetime.fromisoformat(f"{today_str}T{work_end}:00+00:00")

    # Parse busy blocks
    busy = []
    for block in busy_blocks:
        start = parse_datetime(block["start"])
        end = parse_datetime(block["end"])
        # Ensure timezone-aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        busy.append((start, end))

    busy.sort()

    # Find free slots
    free_slots = []
    current = work_start_dt

    for busy_start, busy_end in busy:
        if busy_start > current:
            free_slots.append((current, busy_start))
        current = max(current, busy_end)

    if current < work_end_dt:
        free_slots.append((current, work_end_dt))

    return free_slots

def find_slot(free_slots, duration_min):
    """
    Find the first free slot that can fit a task of given duration (in minutes).
    Returns (start, end) as datetime objects, or None if no slot fits.
    """
    for slot_start, slot_end in free_slots:
        available_min = int((slot_end - slot_start).total_seconds() / 60)
        if available_min >= duration_min:
            return (slot_start, slot_start + timedelta(minutes=duration_min))
    return None

def fit_schedule(tasks: List[Dict], free_slots: List[Tuple]) -> Tuple[List[Dict], List[Dict]]:
    """
    Schedule tasks into free slots, respecting priority and due date.
    Returns (scheduled_tasks, deferred_tasks).
    """
    # Sort by priority, then by due date
    tasks_sorted = sorted(
        tasks,
        key=lambda t: (
            priority_rank(t["priority"]),
            t["due"] or "9999-12-31"  # Tasks with no due date go to the end
        )
    )

    scheduled = []
    deferred = []
    remaining_slots = list(free_slots)

    for task in tasks_sorted:
        duration_with_buffer = task["estimate_min"] + BUFFER_MIN
        slot = find_slot(remaining_slots, duration_with_buffer)

        if slot:
            scheduled.append({
                **task,
                "scheduled_start": slot[0],
                "scheduled_end": slot[1]
            })
            # Remove this slot from available slots
            slot_start, slot_end = slot
            new_slots = []
            for s_start, s_end in remaining_slots:
                if s_end <= slot_start or s_start >= slot_end:
                    new_slots.append((s_start, s_end))
                else:
                    if s_start < slot_start:
                        new_slots.append((s_start, slot_start))
                    if slot_end < s_end:
                        new_slots.append((slot_end, s_end))
            remaining_slots = new_slots
        else:
            deferred.append(task)

    return scheduled, deferred

def calculate_total_demand_and_available_time(tasks: List[Dict], free_slots: List[Tuple]) -> Tuple[float, float]:
    """
    Calculate total requested time (in hours) and total available time (in hours).
    """
    total_requested = sum(t["estimate_min"] for t in tasks) / 60.0
    total_available = sum((end - start).total_seconds() / 3600.0 for start, end in free_slots)
    return total_requested, total_available
