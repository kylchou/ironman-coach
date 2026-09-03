# Ironman Coach

My own training dashboard for Ironman prep. Pulls workouts from Garmin (swim/bike/run), plus
weather and calendar data, and tracks distance/pace/HR/training load/recovery over time. AI
recommendations too, once you drop in an API key.

## Build plan

1. ✅ Connect one workout API (Garmin) + database
2. ✅ Basic dashboard (Next.js, reads from the API)
3. ✅ Weather + calendar data
4. ✅ Training analytics (load, pace/HR trends)
5. ✅ Recovery & fitness scores
6. ✅ AI-generated recommendations & explanations (code's done, just needs your own free API key — see below)
7. ✅ Unified to-do list (manual tasks + Canvas assignments) — not part of the original plan, added this later. Still haven't done the "support other athletes" step from the original plan.

## Stack

- **Backend:** Python 3.12 / FastAPI, SQLAlchemy 2.0, Alembic migrations
- **Database:** PostgreSQL 16 (installed locally, native Windows service, no Docker)
- **Frontend:** Next.js 16 (App Router, TypeScript, Tailwind CSS 4). Server Components fetch
  directly from the backend, nothing client-side for the initial load.

## Project layout

```
ironman-coach/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + router registration
│   │   ├── config.py          Settings, loaded from backend/.env
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models.py          Athlete, Activity ORM models
│   │   ├── schemas.py         Pydantic response models
│   │   ├── routers/
│   │   │   ├── garmin_auth.py   Reports cached Garmin session status
│   │   │   └── activities.py    Sync from Garmin + list from DB
│   │   └── services/
│   │       └── garmin_client.py  Garmin Connect API wrapper
│   ├── scripts/
│   │   └── garmin_login.py    Interactive one-time login (run manually)
│   ├── alembic/                Migrations
│   ├── requirements.txt
│   └── .env                    Local secrets (gitignored) — copy from .env.example
└── frontend/
    ├── src/app/page.tsx        Dashboard (Server Component, fetches from backend)
    ├── src/components/         SummaryCard, SportTabs, ActivityTable
    ├── src/lib/                api.ts (fetch), format.ts, summary.ts
    └── .env.local               API_BASE_URL (gitignored)
```

One thing to know if you're poking around this repo with an AI assistant: Next.js 16 is recent
enough that a lot of training data is stale on it (`params`/`searchParams` are Promises now,
among other changes). There's an `AGENTS.md` in `frontend/` that says the same thing. If
something looks off, check `frontend/node_modules/next/dist/docs/` before trusting old habits.

## One-time setup already done on this machine

- Python 3.12, Node.js LTS, PostgreSQL 16, all via winget
- Database `ironman_coach` created, with its own app role `ironman_app` (password's in
  `backend/.env`, not committed)
- Python virtualenv at `backend/.venv`, deps installed including `garminconnect` (the unofficial
  Garmin Connect client)
- Initial Alembic migration applied (`athletes`, `activities` tables)

## Why Garmin instead of Strava

Strava started requiring a paid Summit subscription for API access in June 2026, which felt
silly just to read my own data back out. Garmin doesn't have a real public API for personal use
either, so this uses `garminconnect`, a library that talks to the same endpoints the Garmin
Connect app/website use, logged in as your own account. It's unofficial and could break if
Garmin changes something on their end — if `/activities/sync` suddenly stops working, check
https://github.com/cyberjunky/python-garminconnect before assuming it's my code.

## Weather

[Open-Meteo](https://open-meteo.com) — free, no signup, no API key. Three endpoints:

- `GET /weather/current` — live conditions + 7-day forecast (not stored, changes constantly)
- `POST /weather/sync?days_back=N` — backfills `daily_weather` for the past N days so it can
  later be joined against training history (was it hot/rainy that day?). Already ran this once
  for the last 60 days.
- `GET /weather/daily?start=&end=` — reads the stored history back out

Location is auto-derived from your most recent GPS-tagged activity, unless you set
`LOCATION_LAT`/`LOCATION_LON` in `backend/.env`. Heads up: that means weather follows wherever
your last outdoor activity was recorded — right now that's Athens, GA ("Athens Running"), not my
usual Chicago area, since it's literally just picking the most recent one. If you want stable
weather for home regardless of travel, set the lat/lon explicitly.

## Calendar

Reads your primary Google Calendar (read-only) via plain OAuth2 + REST, **not** Google's official
`google-api-python-client`/`google-auth` libraries. Those pull in `cryptography`, and this
machine's Application Control policy blocks its native Rust extension — the import just fails
with "An Application Control policy has blocked this file". The web-server OAuth flow doesn't
actually need any client-side crypto though, it's just JSON over HTTPS, so plain `httpx` sidesteps
the whole problem. See `services/calendar_client.py`.

- `GET /auth/google/login` — open in a browser, approve access, get redirected back
- `GET /auth/google/status` — check the connection
- `GET /calendar/events?days=7` — upcoming events on your primary calendar

### One-time Google Cloud Console setup (you'll need to do this yourself)

1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a new project
   (e.g. "Ironman Coach").
2. **APIs & Services → Library** → search "Google Calendar API" → **Enable**.
3. Set up the consent screen (Google renamed this to "Google Auth Platform" at some point —
   if you can't find it in the sidebar, just go to
   `https://console.cloud.google.com/auth/audience?project=<your-project-number>`):
   - User type: **External**
   - Fill in app name, your email as support/developer contact
   - **Audience tab → Test users**: add your Google account, or login fails with
     `Error 403: access_denied` since the app stays unpublished. Skip this if you're logging in
     with the same account that owns the Cloud project — owners can always test their own app.
   - Test-user authorizations expire after 7 days (Google's policy, not mine) — if
     `/calendar/events` starts throwing an auth error after about a week, just redo
     `/auth/google/login`.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
   - Copy the **Client ID** and **Client Secret** into `backend/.env`

## Training analytics

- `GET /analytics/weekly-load?weeks=12` — training load per week, by sport (Run/Ride/Swim)
- `GET /analytics/trends?sport=Run&weeks=12` — weekly avg pace/speed and HR for one sport

Note that "load" here is a self-calibrating estimate, not real TRIMP. Real TRIMP needs your
resting HR and a lab-measured max HR, and I haven't configured either. Instead each activity's
intensity is estimated relative to the highest heart rate seen anywhere in your own synced
history, squared to weight higher intensity harder (roughly mirroring TRIMP's exponential
curve), then multiplied by duration. Activities without HR data just fall back to a fixed
moderate-intensity guess so they still count toward weekly volume. The formula and reasoning are
in `backend/app/services/training_load.py` — might be worth revisiting if the recovery/fitness
scores ever need something more rigorous.

The **Analytics** page (`/analytics`) charts this: a stacked bar of weekly load by sport, plus
pace/HR trend lines with a sport switcher. Built following the `dataviz` skill's approach — fixed
color slots for Run/Ride/Swim (never cycled), checked with its `validate_palette.js` rather than
eyeballed.

## Recovery & readiness score

- `GET /readiness/today` — 0-100 composite score + label (Primed / Ready / Manage fatigue /
  Recover), shown as the hero number on the dashboard. Every component is explained right there
  in the UI — what CTL/ATL/TSB actually mean, where the resting-HR baseline comes from — plus a
  full sleep-stage breakdown (deep/light/REM/awake, HR, respiration, SpO2, stress) pulled from
  whatever Garmin's sleep API exposes.
- `GET /readiness/history?days=90` — daily Fitness (CTL) / Fatigue (ATL) / Form (TSB), not
  charted anywhere yet (would make a nice Performance-Management-Chart-style addition to
  `/analytics` at some point)
- `GET /readiness/resting-hr?days=N` — daily resting HR for the last N days, powers the
  expandable "Resting HR history" section (This week / Last 4 weeks)

What it's built from, blended by weight (if a component's missing, it's just left out and the
rest get renormalized instead of the whole score failing):

| Component | Weight | Source |
|---|---|---|
| Training Stress Balance (Form) | 35% | Computed from your own synced activities — see below |
| HRV status | 30% | Garmin (`BALANCED` / `UNBALANCED` / `LOW`) — needs a fairly recent HRV-capable watch |
| Sleep score | 25% | Garmin's own 0-100 sleep score |
| Resting HR vs. 30-day baseline | 10% | Garmin |

Fitness/Fatigue/Form uses the same model as TrainingPeaks' Performance Management Chart
(Banister impulse-response): CTL is a 42-day rolling average of daily training load, ATL is the
7-day version, TSB = CTL − ATL. Again, not clinical TRIMP — see `training_load.py`. Probably
worth calibrating against how you actually feel once you've used it for a while.

A real bug I caught before shipping this: the per-activity load formula was using minutes where
the TSS-style convention it follows expects hours, so every load number was inflated about 60x.
Harmless for the relative week-to-week bar chart, but it broke the readiness score outright — TSB
was hitting +724 (should top out around +25-30) and permanently pegged the Form component at
100, killing its signal. Fixed in `training_load.py`, both now agree.

## AI coach

`POST /coach/brief` gathers everything the app already knows — readiness score and its
components, training load over the last 4 weeks, activities from the last 14 days, the 4-day
weather forecast, next 7 days of calendar events — into one prompt and asks an LLM to explain
your current state in plain language and suggest what to do next. Shows up on the dashboard as
an "AI Coach" card with a button (not auto-loaded on page view since it's a real API call, so you
trigger it on demand).

Uses Gemini, not Claude. Claude's API is pay-as-you-go — cheap, a few cents a call, but still not
$0 — and Gemini has an actually-free tier, no credit card, just a Google account. Also skips
Google's official Python client (`google-generativeai`) in favor of plain `httpx` REST, same
`cryptography`-DLL problem as the Calendar section above.

The model's configurable (`GEMINI_MODEL` in `.env`, default `gemini-2.5-flash`) since Google
moves its free-tier lineup around a lot — if it ever gets deprecated, just bump the env var
instead of touching code.

### Setup

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey), sign in with a
   Google account, create an API key. No credit card needed.
2. Add it to `backend/.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Restart the backend, then click **Get today's brief** on the dashboard.

## Tasks (added after the original plan)

One unified to-do list — manual tasks and synced Canvas assignments together, soonest due date
first, completed items sink to the bottom instead of disappearing. This is the start of turning
the app into more of a daily hub (training + school + life) instead of just training.

- `GET /tasks?include_completed=` / `POST /tasks` / `PATCH /tasks/{id}` / `DELETE /tasks/{id}`
  — plain CRUD for manual tasks
- `POST /tasks/sync-canvas` — pulls whatever Canvas's own "to-do" list considers still needing
  action (not every assignment that's ever existed) and upserts it into the same table

Everything lives in one `tasks` table (`source` = `"manual"` or `"canvas"`) instead of separate
Assignment/Todo tables — the whole point is one list instead of checking Canvas and a to-do app
separately.

Fair warning: the Canvas integration is unverified. I built it off documented API shapes
(`backend/app/services/canvas_client.py`) but haven't actually run it against a real
account/token yet, unlike everything else in this app which got checked against live data before
I called it done. First real sync will be the real test — expect to fix a field name or two if
Canvas's actual response doesn't match the docs.

### Setup

1. In Canvas: **Account** (left sidebar) → **Settings** → scroll to **Approved Integrations** →
   **+ New Access Token**. Purpose can be anything, leave expiry blank → **Generate Token**.
   Copy it now, Canvas only shows it once.
2. Add to `backend/.env`:
   ```
   CANVAS_DOMAIN=your-school.instructure.com
   CANVAS_ACCESS_TOKEN=your_token_here
   ```
3. Restart the backend, then click **Sync Canvas** on the dashboard's To-Do card.

## What you still need to do

### 1. Log in to Garmin (one-time, interactive)

```bash
cd backend
.venv\Scripts\activate
python scripts/garmin_login.py
```

It'll ask for your Garmin email and password directly at the terminal (and an MFA code if Garmin
sends you one). Nothing goes anywhere but Garmin's own login endpoint, and the password never
touches disk. It caches a session token to `backend/.garmin_tokens/` (gitignored) so the API
server doesn't need your password again after that. Re-run this whenever the cached session
expires or gets revoked.

### 2. Run the backend

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 3. Confirm the connection

```bash
curl http://localhost:8000/auth/garmin/status
```

### 4. Pull your activities

```bash
curl -X POST "http://localhost:8000/activities/sync?pages=10"
curl "http://localhost:8000/activities?sport_type=Run"
```

Interactive API docs are always at http://localhost:8000/docs once the server's running.

### 5. Set up Google Calendar (see "Calendar" above) and connect it

Once `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` are in `backend/.env` and the backend's restarted:

```bash
# open in a browser, not curl -- it's an interactive consent screen
http://localhost:8000/auth/google/login
```

```bash
curl http://localhost:8000/auth/google/status
curl "http://localhost:8000/calendar/events?days=7"
```

### 6. Set up Canvas (see "Tasks" above) and sync

Once `CANVAS_ACCESS_TOKEN` is in `backend/.env` and the backend's restarted:

```bash
curl -X POST http://localhost:8000/tasks/sync-canvas
```

### 7. Run the frontend (second terminal, backend still running)

```bash
cd frontend
npm run dev
```

Open http://localhost:3000 — summary cards for the last 28 days by sport, plus a filterable
table of recent activities. If PowerShell blocks `.venv\Scripts\activate` with a "running
scripts is disabled" error, either call `.venv\Scripts\python.exe` directly, or just run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once — you'll hit the same wall with
npm/npx otherwise anyway.

## Notes / decisions

- Postgres is installed natively, not Docker, to skip WSL2/Hyper-V setup on this machine. Could
  containerize it later if that ever matters.
- The full raw Garmin payload is stored per activity (`raw` JSONB column) alongside the extracted
  columns, so later work can backfill new fields without a re-sync.
- `Activity` has a `source` column (currently always `"garmin"`) so another source (Strava, if I
  ever get API access) could get added later without a schema change.
- Right now most endpoints just assume one athlete, one Garmin account. That'll need to change
  before "other athletes" support, which is still on the original plan and hasn't happened yet.
- Garmin occasionally reports a corrupted `movingDuration` on pool swims (saw ~193 hours for a
  61-minute swim once). `activities.py` clamps moving time to elapsed time when that happens.
  Elevation gain/loss has shown clearly-wrong values too on some activities — not fixed since
  nothing depends on it yet, but flagging it in case analytics ever needs elevation.
- **Windows dev-server quirk:** running `next dev` from a directory referenced by its 8.3 short
  path (like `KYLERC~1` instead of `Kyler Chou`) crashes Next's file watcher with a libuv
  assertion (`fs-event.c` path mismatch). Always launch it via the normal long path.
- **This machine's Application Control policy blocks the `cryptography` package's native Rust
  extension.** Found this while adding Google Calendar — `import google_auth_oauthlib` fails
  with "An Application Control policy has blocked this file". Any future dependency that pulls in
  `cryptography` (directly or transitively — a lot of auth/crypto-adjacent packages do) will hit
  the same wall. Worth checking early if a new library's import fails for no obvious reason.
- **Frontend date-parsing gotcha:** a bare `"YYYY-MM-DD"` string (no time/offset — resting-HR
  history dates, for example) parses as UTC midnight per the JS spec. Formatting it with
  `toLocaleDateString()` then renders in the browser's local timezone, which silently shows the
  previous day anywhere west of UTC. Full ISO timestamps (with an offset, like activity
  `start_date`) don't have this problem, only bare dates do. Fix is anchoring to local noon first
  (`` new Date(`${isoDate}T12:00:00`) ``) before formatting — see `formatBareDate` /
  `formatWeekLabel` / `formatShortDate` in `frontend/src/lib/format.ts`, and use the bare-date
  version for any new bare-date field instead of reaching for `formatDate`.
- **Backend `created_at` timezone bug (fixed 2026-09-01):** every model's `created_at` used
  `default=datetime.utcnow`, a naive datetime with no timezone tag. psycopg2 stores a naive
  datetime into a `timestamptz` column using the session's local timezone, not literal UTC, so
  every `created_at` in the app (Athlete, Activity, DailyWeather, and initially Task) was
  silently off by the local UTC offset. Caught it by comparing a task's `created_at` against its
  `completed_at` (already correct, using `datetime.now(timezone.utc)`) and finding a 4-hour gap
  between two timestamps set milliseconds apart. Fixed with a shared `_utcnow()` helper in
  `models.py` — use that for any new `created_at`-style default, never bare `datetime.utcnow`.
  Old rows from before the fix keep their wrong value (harmless, nothing reads `created_at` for
  business logic, only display/sort tie-breaking) — only new rows are correct.
