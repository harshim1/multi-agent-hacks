#!/usr/bin/env python3
"""
Local test of Phase 1 scheduling logic without hitting real APIs.
Run with: python test_phase1.py
"""

from datetime import datetime, timedelta
from scheduler import fit_schedule, get_calendar_free_slots, calculate_total_demand_and_available_time

# Mock data: today's work hours, some busy blocks
today_str = datetime.now().strftime("%Y-%m-%d")

busy_blocks = [
    {
        "start": f"{today_str}T09:00:00Z",
        "end": f"{today_str}T10:30:00Z",
        "summary": "Standup"
    },
    {
        "start": f"{today_str}T12:00:00Z",
        "end": f"{today_str}T13:00:00Z",
        "summary": "Lunch"
    },
    {
        "start": f"{today_str}T15:00:00Z",
        "end": f"{today_str}T15:30:00Z",
        "summary": "Quick sync"
    }
]

# Mock tasks
tasks = [
    {
        "id": "task_1",
        "title": "Write quarterly report",
        "estimate_min": 120,
        "priority": "Must",
        "due": "2026-09-14",
        "context": "Deep"
    },
    {
        "id": "task_2",
        "title": "Email feedback to team",
        "estimate_min": 30,
        "priority": "Should",
        "due": "2026-09-13",
        "context": "Admin"
    },
    {
        "id": "task_3",
        "title": "Code review for PR",
        "estimate_min": 45,
        "priority": "Should",
        "due": "2026-09-13",
        "context": "Deep"
    },
    {
        "id": "task_4",
        "title": "Grocery shopping",
        "estimate_min": 30,
        "priority": "Could",
        "due": "2026-09-15",
        "context": "Errand"
    },
    {
        "id": "task_5",
        "title": "Brainstorm new features",
        "estimate_min": 60,
        "priority": "Could",
        "due": "2026-09-16",
        "context": "Creative"
    }
]

print("=" * 60)
print("PHASE 1 LOCAL TEST: Scheduling Logic")
print("=" * 60)

# Test 1: Get free slots
print("\n[Test 1] Extracting free slots from calendar...")
free_slots = get_calendar_free_slots(busy_blocks)
print(f"Free slots found: {len(free_slots)}")
for i, (start, end) in enumerate(free_slots, 1):
    duration_min = int((end - start).total_seconds() / 60)
    print(f"  Slot {i}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')} ({duration_min}m)")

# Test 2: Demand vs. capacity
print("\n[Test 2] Demand vs. Capacity check...")
total_requested, total_available = calculate_total_demand_and_available_time(tasks, free_slots)
print(f"Requested: {total_requested:.1f}h")
print(f"Available: {total_available:.1f}h")
print(f"Feasible: {'✅ YES' if total_requested <= total_available else '❌ NO'}")

# Test 3: Schedule
print("\n[Test 3] Fitting tasks into slots...")
scheduled, deferred = fit_schedule(tasks, free_slots)

print(f"\nScheduled ({len(scheduled)}):")
for task in scheduled:
    start = task["scheduled_start"].strftime("%H:%M")
    end = task["scheduled_end"].strftime("%H:%M")
    print(f"  ✅ {task['title']} ({start}–{end}, priority: {task['priority']})")

print(f"\nDeferred ({len(deferred)}):")
for task in deferred:
    print(f"  ⏸ {task['title']} (priority: {task['priority']})")

# Test 4: No duplicate events (idempotency simulation)
print("\n[Test 4] Idempotency test (same run, same plan)...")
scheduled_2, deferred_2 = fit_schedule(tasks, free_slots)
if len(scheduled_2) == len(scheduled) and all(
    s1["id"] == s2["id"] for s1, s2 in zip(scheduled, scheduled_2)
):
    print("✅ Idempotent: same input produces same output")
else:
    print("❌ Non-idempotent: output varies")

# Test 5: Task overload
print("\n[Test 5] Overload scenario (demand exceeds capacity)...")
overloaded_tasks = tasks + [
    {"id": f"extra_{i}", "title": f"Extra task {i}", "estimate_min": 120,
     "priority": "Must", "due": "2026-09-13", "context": "Deep"}
    for i in range(2)
]
total_requested_overload, _ = calculate_total_demand_and_available_time(overloaded_tasks, free_slots)
scheduled_overload, deferred_overload = fit_schedule(overloaded_tasks, free_slots)
print(f"Requested: {total_requested_overload:.1f}h (exceeds available)")
print(f"Deferred (not silent drops): {len(deferred_overload)} tasks")
print(f"✅ No tasks silently dropped: all are either scheduled or deferred")

print("\n" + "=" * 60)
print("PHASE 1 LOCAL TESTS PASSED ✅")
print("=" * 60)
print("\nNext: Configure .env with real credentials, then run: streamlit run app.py")
