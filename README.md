# Tempo — Planning Support Agent

**Tempo detects when a planned day's demand doesn't match the real capacity available, and makes that mismatch visible instead of hiding it behind a schedule that looks fine.**

## Core Idea

Most schedulers optimize for a fuller calendar. Tempo does the opposite: it reads your tasks, checks your actual calendar availability, and refuses to overbook. If a day is infeasible, it says so—explicitly showing which tasks fit and which don't, and why.

## What Tempo Is (and Isn't)

Tempo is a **planning-support prototype**, not a diagnostic, therapeutic, or medical tool. It observes your own task history—estimates, actuals, reschedules—and uses that history to calibrate future plans and explain scheduling decisions. It does not infer a diagnosis, assess symptoms, or make claims about your cognitive state. Every action requires your approval, and every automated write is logged and reversible.

## Setup

### Prerequisites

- Python 3.8+
- Notion workspace with an internal integration token
- Google Cloud project with Calendar and Sheets APIs enabled
- A Google Sheet to store ledger and evaluation data
- A dedicated test Google Calendar (recommend naming it `Tempo Demo`)

### Step 1: Configure Notion

1. Create a Notion database with these properties:
   - **Title** (text)
   - **Due** (date)
   - **Estimate** (number, in minutes)
   - **Context** (select: Deep, Admin, Creative, Errand)
   - **Priority** (select: Must, Should, Could)
   - **Status** (select: Inbox, Planned, Deferred, Done)
   - **Calendar Event ID** (text, filled by Tempo)

2. Create an internal integration in Notion, get the token, and share the database with it.

### Step 2: Configure Google Cloud

1. Create a Google Cloud project.
2. Enable the Calendar API and Sheets API.
3. Create OAuth credentials (type: Desktop application).
4. Download the credentials as `credentials.json`.

### Step 3: Create Google Sheet and Calendar

1. Create a Google Sheet with exactly two tabs:
   - **Ledger** (columns: run_id, task_id, idempotency_key, calendar_event_id, status, timestamp)
   - **Evaluation** (columns: scenario, result, metric_name, metric_value)

2. Create a dedicated test calendar in Google Calendar (e.g., `Tempo Demo`).

### Step 4: Fill in `.env`

Copy `.env.example` to `.env` and fill in your actual values:

```bash
NOTION_TOKEN=your_token_here
NOTION_DATABASE_ID=your_db_id_here
GOOGLE_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CALENDAR_ID=your_calendar_id_here
ANTHROPIC_API_KEY=sk-... (Phase 3 only)
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`. On first run, you'll be prompted to authenticate with Google. The token is cached locally.

## Architecture

### Phase 1: Minimum Viable Loop (Complete)

- Read tasks from Notion (Status = Inbox)
- Read busy blocks from Google Calendar
- Schedule tasks into free slots, respecting priority and due date
- Write events to Calendar, update Notion, log to Sheets Ledger
- UI: "Generate & Write Plan" button, before/after display

**Definition of done:** Click the button, see real Calendar events, Notion updates, and Sheets rows—no crashes on normal days, clean "Deferred" entries when overloaded.

### Phase 2: Reliability + Differentiation (Planned)

- Demand vs. capacity check (explicit mismatch display)
- Transition-cost clustering (group same-context tasks, measure context-switch cost)
- Idempotent execution (check Ledger before writing, no duplicate events)
- Failure recovery (simulate Calendar failure, recover cleanly with retry)
- Five test scenarios with pass/fail results logged to Evaluation tab

**Definition of done:** All 5 scenarios pass, live failure recovery works, transition-cost reduction is measurable.

### Phase 3: Calibration + Polish (Planned)

- Seeded history (12–15 fake task records with actual durations)
- Calibration (personalized duration estimates: 0.6 × user_estimate + 0.4 × median_actual)
- Friction labeling (plain rule-based tags for deferred tasks, no invented scoring formulas)
- LLM explanation (isolated, with deterministic fallback—never on critical path)
- Baseline comparison (naive vs. Tempo transition costs, side by side)
- Documentation (README, reliability brief, positioning statement)

**Definition of done:** Calibration reveal works, friction labels show correctly, LLM has working fallback, docs are accurate to what's built.

## Non-Negotiable Engineering Rules

These rules protect the integrity of what Tempo claims to do:

1. **Deterministic scheduling owns:** calendar availability, overlap checks, duration math, feasibility/deferral decisions, idempotency, write authorization. No randomness.

2. **LLM isolation (Phase 3 only):** The LLM turns an already-decided outcome into a one-sentence explanation. It never decides what gets scheduled, never touches write calls. If it errors or times out, fall back to a deterministic template—the app must keep working.

3. **Idempotency:** Before creating a Calendar event, check the Ledger for an existing successful write with the same idempotency key. Never create a duplicate on rerun.

4. **No silent drops:** If a task doesn't fit, it becomes an explicit "Deferred" state, visible in the output. Never just disappears.

5. **No invented scoring formulas:** If you need to rank or tag something (like why a task keeps failing), use a plain, explainable if/else rule, not a weighted composite score with made-up weights.

6. **No clinical language:** Never claim to "detect ADHD," "treat," "diagnose," or "detect cognitive overload." Frame everything as: observes the user's own task history, calibrates estimates from it, explains reasoning, requires approval before writing.

## Data Model (Fixed)

**Notion task properties:**
- Title, Due (date), Estimate (minutes), Context, Priority, Status, Calendar Event ID

**Sheets Ledger columns:**
- run_id, task_id, idempotency_key, calendar_event_id, status, timestamp

**Sheets Evaluation columns:**
- scenario, result (pass/fail), metric_name, metric_value

**Idempotency key format:**
```
f"{run_id}:{task_id}:{slot_start}"
```
Plain string, human-readable, not a hash.

## Testing

Local unit test (no APIs required):

```bash
python test_phase1.py
```

This verifies scheduling logic, demand/capacity calculation, idempotency, and deferral behavior.

## Project Files

- `app.py` — Streamlit UI
- `scheduler.py` — Core deterministic scheduling logic
- `notion_client.py` — Notion database read/write
- `google_calendar_client.py` — Calendar read/write
- `google_sheets_client.py` — Ledger and Evaluation tab writes
- `test_phase1.py` — Local verification of Phase 1 logic
- `.env.example` — Secrets template
- `requirements.txt` — Python dependencies

## Demos & Materials

- **[Live Demo Video](https://www.loom.com/share/8c59ce8a29b74f10b2bc53dc1c73c79b)** — Walkthrough of Phase 1 scheduling, demand/capacity detection, and the three-phase vision
- **[Pitch Deck](./TempoPitchDeckpptx.pptx)** — Full presentation with research grounding, positioning, and demo script
- **Screenshots** — UI flow, scheduled vs. deferred tasks, Ledger logging

## Current Status

**Phase 1:** Scaffold complete, local tests pass. Ready for credential configuration and live demo.

## Known Limitations (Current)

- Seed history in Phase 3 will be small and demo-only, not a real user's history.
- Context-based task tagging (Deep, Admin, Creative, Errand) is rule-of-thumb, not personalized.
- System recommends; does not autonomously control the calendar.
- No task splitting—a task must fit within a single free calendar slot or is deferred entirely.
- Transition-cost matrix is fixed; doesn't learn from user feedback.

## License

Built for hackathon evaluation. Code is example/demo work.
https://www.loom.com/share/8c59ce8a29b74f10b2bc53dc1c73c79b

