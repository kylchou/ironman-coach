# Ironman Coach

A personal training dashboard for Ironman prep: pulls workouts from Garmin (swim/bike/run),
weather, and calendar data; tracks distance/pace/HR/training load/recovery; and will
eventually recommend workouts and explain your data via AI.

## Build plan

1. ✅ **Connect one workout API (Garmin) + database**
2. ✅ **Basic dashboard (Next.js, reads from the API)**
3. ✅ **Weather + calendar data**
4. ✅ **Training analytics (load, pace/HR trends)**
5. ✅ **Recovery & fitness scores**
6. ✅ **AI-generated recommendations & explanations** (code done -- needs your own free API key, see below)
7. ✅ **Unified to-do list (manual tasks + Canvas assignments)** -- extends the original plan; not
   yet: generalizing beyond a single athlete

## Stack

- **Backend:** Python 3.12 / FastAPI, SQLAlchemy 2.0, Alembic migrations
- **Database:** PostgreSQL 16 (installed locally as a native Windows service)
- **Frontend:** Next.js 16 (App Router, TypeScript, Tailwind CSS 4) — Server Components fetch
  directly from the backend, no client-side data fetching yet

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

**Note:** Next.js 16 is new enough that Claude's training data doesn't reliably cover it —
its own `AGENTS.md` (auto-generated in `frontend/`) says as much. Check
`frontend/node_modules/next/dist/docs/` for the real API before assuming old patterns
(e.g. `params`/`searchParams` are now Promises) still apply.

## One-time setup already done on this machine

- Python 3.12, Node.js LTS, PostgreSQL 16 installed via winget
- Database `ironman_coach` created, with a dedicated app role `ironman_app`
  (password lives in `backend/.env`, not committed)
- Python virtualenv created at `backend/.venv`, dependencies installed (including
  `garminconnect`, the unofficial Garmin Connect client library)
- Initial Alembic migration created & applied (`athletes`, `activities` tables)

## Why Garmin instead of Strava

Strava's Developer Program started requiring a paid Strava subscription for API access in
June 2026, which isn't worth it just to read your own data back out. Garmin doesn't offer a
free public API for personal use either, so this uses the `garminconnect` library, which
talks to the same endpoints the Garmin Connect app/website use, authenticated as your own
account. It's unofficial and could break if Garmin changes something internally — if
`/activities/sync` suddenly fails, check https://github.com/cyberjunky/python-garminconnect
for API changes before assuming it's a bug in this code.

## Weather

Uses [Open-Meteo](https://open-meteo.com) — free, no signup, no API key. Two endpoints:

- `GET /weather/current` — live current conditions + 7-day forecast (not stored, changes
  constantly)
- `POST /weather/sync?days_back=N` — backfills `daily_weather` for the past N days, so it can
  later be joined against training history (was it hot/rainy on the day of a given workout).
  Already run once for the last 60 days.
- `GET /weather/daily?start=&end=` — read the stored history back out

**Location** is auto-derived from your most recent GPS-tagged activity (`startLatitude`/
`startLongitude` in the raw Garmin payload) unless `LOCATION_LAT`/`LOCATION_LON` are set in
`backend/.env`. Worth knowing: this means weather follows wherever your last recorded outdoor
activity was — right now that's Athens, GA (from "Athens Running"), not your usual Chicago-area
base, since it's literally just "most recent". If you want stable weather for your home base
regardless of travel, set `LOCATION_LAT`/`LOCATION_LON` explicitly.

## Calendar

Reads your primary Google Calendar (read-only) via plain OAuth2 + REST calls, **not** Google's
official `google-api-python-client`/`google-auth` libraries -- those pull in the `cryptography`
package, whose native Rust extension is blocked by this machine's Application Control policy
(confirmed while building this: the import itself fails with "An Application Control policy has
blocked this file"). The web-server OAuth flow needs no client-side crypto -- it's just JSON over
HTTPS -- so `httpx` calls avoid the problem entirely. See `services/calendar_client.py`.

- `GET /auth/google/login` — open in a browser, approve access, get redirected back
- `GET /auth/google/status` — check the connection
- `GET /calendar/events?days=7` — upcoming events on your primary calendar

### One-time Google Cloud Console setup (you'll need to do this yourself)

1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a new project
   (e.g. "Ironman Coach").
2. **APIs & Services → Library** → search "Google Calendar API" → **Enable**.
3. Configure the consent screen (Google renamed this "Google Auth Platform" sometime in
   2025/2026 — sidebar wording varies, so if you can't find it, go straight to
   `https://console.cloud.google.com/auth/audience?project=<your-project-number>` instead):
   - User type: **External**
   - Fill in app name, your email as support/developer contact
   - **Audience tab → Test users**: add your Google account email — required, or login fails
     with `Error 403: access_denied`, since this app stays unpublished. **Skip this entirely if
     the account you'll log in with is the same one that owns the Cloud project** — project
     owners can always test the app, test-user status is only for other accounts.
   - Note: test-user authorizations expire after 7 days per Google's policy — if
     `/calendar/events` starts failing with an auth error after a week or so, just redo the
     `/auth/google/login` step below.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
   - Copy the **Client ID** and **Client Secret** into `backend/.env`

## Training analytics

- `GET /analytics/weekly-load?weeks=12` — training load per week, broken down by sport (Run/Ride/Swim)
- `GET /analytics/trends?sport=Run&weeks=12` — weekly avg pace/speed and heart rate for one sport

**"Load" is a self-calibrating estimate, not clinical TRIMP.** Real TRIMP needs the athlete's
resting HR and a lab-measured max HR, neither of which is configured anywhere in this app.
Instead, each activity's intensity is estimated relative to the highest heart rate observed
anywhere in your own synced history, squared to penalize higher intensity more than low
(loosely mirroring TRIMP's exponential weighting), then multiplied by duration. Activities with
no HR data fall back to a fixed moderate-intensity assumption so they still count toward
weekly volume. See `backend/app/services/training_load.py` for the exact formula and reasoning
— worth revisiting if Phase 5's recovery/fitness scores want something more rigorous.

The dashboard's **Analytics** page (`/analytics`) charts this: a stacked bar of weekly load by
sport, plus pace/HR trend lines with a sport switcher. Charts were built following the
`dataviz` skill's method (validated categorical palette — Run/Ride/Swim get fixed slots 1/2/3,
never cycled — checked with its `validate_palette.js` script rather than eyeballed).

## Recovery & readiness score

- `GET /readiness/today` — a 0-100 composite score + label (Primed / Ready / Manage fatigue /
  Recover), shown as the hero number at the top of the dashboard, with every component
  explained inline in the UI (not just labeled — the card spells out what CTL/ATL/TSB mean and
  where the resting-HR baseline comes from) and a full sleep-stage breakdown (deep/light/REM/
  awake, HR, respiration, SpO2, stress) pulled from everything Garmin's sleep API exposes
- `GET /readiness/history?days=90` — daily Fitness (CTL) / Fatigue (ATL) / Form (TSB) series,
  not yet charted anywhere (would make a nice Performance-Management-Chart-style addition to
  `/analytics` later)
- `GET /readiness/resting-hr?days=N` — daily resting HR for the last N days; powers an
  expandable "Resting HR history" section on the dashboard (Today / This week / Last 4 weeks)

**What it's built from**, blended by weight (missing components are simply left out and the
rest renormalized, rather than the score failing outright):

| Component | Weight | Source |
|---|---|---|
| Training Stress Balance (Form) | 35% | Computed from your own synced activities — see below |
| HRV status | 30% | Garmin (`BALANCED` / `UNBALANCED` / `LOW`) — needs a fairly recent HRV-capable watch |
| Sleep score | 25% | Garmin's own 0-100 sleep score |
| Resting HR vs. 30-day baseline | 10% | Garmin |

**Fitness/Fatigue/Form** uses the same model TrainingPeaks' Performance Management Chart is
built on (Banister impulse-response): CTL is a 42-day rolling average of daily training load,
ATL the 7-day version, TSB = CTL − ATL. This is **not** clinical TRIMP — see
`backend/app/services/training_load.py` for why. Worth calibrating against how you actually
feel once you've used it a while.

**A real bug caught before shipping:** the per-activity load formula used minutes where the
TSS-style convention it's supposed to follow expects hours, inflating every load number ~60x.
Harmless for Phase 4's relative week-to-week bar chart, but it broke Phase 5 outright — TSB hit
+724 (should top out around +25-30) and permanently saturated the readiness score's Form
component at 100, destroying its signal. Fixed in `training_load.py`; both phases now agree.

## AI coach

`POST /coach/brief` gathers everything the app already knows -- readiness score and its
components, training load over the last 4 weeks, activities from the last 14 days, the 4-day
weather forecast, and the next 7 days of calendar events -- into one prompt and asks an LLM to
explain your current state in plain language and suggest what to do next. Shown on the dashboard
as an "AI Coach" card with a button (deliberately not auto-loaded on page view -- it's a real
API call, triggered on demand).

**Uses Gemini, not Claude.** Claude's API is pay-as-you-go (cheap here -- a few cents a call --
but not $0); Gemini has a genuinely free tier (no credit card, just a Google account). Also
avoids Google's *official* Python client libraries (`google-generativeai`) in favor of plain
`httpx` REST calls, for the same `cryptography`-DLL-blocked reason documented in the Calendar
section above.

The model is configurable (`GEMINI_MODEL` in `.env`, default `gemini-2.5-flash`) since Google's
free-tier lineup moves fast -- if it ever gets deprecated or moved off the free tier, bump this
rather than changing code.

### Setup

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey), sign in with a
   Google account, create an API key. No credit card needed.
2. Add it to `backend/.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Restart the backend, then click **Get today's brief** on the dashboard.

## Tasks (Phase 7 -- beyond the original plan)

One unified to-do list -- manual tasks and synced Canvas assignments together, soonest due
date first, completed items sink to the bottom rather than disappearing. This is the start of
turning the app into more of a daily hub (training + school + life) rather than training-only.

- `GET /tasks?include_completed=` / `POST /tasks` / `PATCH /tasks/{id}` / `DELETE /tasks/{id}`
  — plain CRUD for manual tasks
- `POST /tasks/sync-canvas` — pulls assignments Canvas considers still needing action (its own
  "to-do" concept, not every assignment that ever existed) and upserts them into the same table

Everything lives in one `tasks` table (`source` = `"manual"` or `"canvas"`) rather than separate
Assignment/Todo tables — the whole point is one list instead of checking Canvas and a to-do app
separately.

**Canvas integration is unverified** — built from documented API shapes
(`backend/app/services/canvas_client.py`), not checked against a real account/token like
everything else in this codebase was before being called done. First real sync will be the real
test; expect to fix field-name mismatches if Canvas's actual response differs from the docs.

### Setup

1. In Canvas: **Account** (left sidebar) → **Settings** → scroll to **Approved Integrations** →
   **+ New Access Token**. Purpose can be anything, leave expiry blank → **Generate Token**.
   Copy it now — Canvas only shows it once.
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

It'll ask for your Garmin email and password directly at the terminal (and an MFA code, if
Garmin sends you one) — nothing is sent anywhere but Garmin's own login endpoint, and the
password is never written to disk. It caches a session token to `backend/.garmin_tokens/`
(gitignored) so the API server never needs your password again. Re-run this script any time
that cached session expires or gets revoked.

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

Interactive API docs are always at http://localhost:8000/docs once the server is running.

### 5. Set up Google Calendar (see "Calendar" section above) and connect it

Once `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` are in `backend/.env` and the backend has
restarted to pick them up:

```bash
# open in a browser, not curl -- it's an interactive consent screen
http://localhost:8000/auth/google/login
```

```bash
curl http://localhost:8000/auth/google/status
curl "http://localhost:8000/calendar/events?days=7"
```

### 6. Set up Canvas (see "Tasks" section above) and sync

Once `CANVAS_ACCESS_TOKEN` is in `backend/.env` and the backend has restarted:

```bash
curl -X POST http://localhost:8000/tasks/sync-canvas
```

### 7. Run the frontend (in a second terminal, backend still running)

```bash
cd frontend
npm run dev
```

Open http://localhost:3000 — summary cards for the last 28 days by sport, plus a filterable
table of recent activities. If PowerShell blocks `.venv\Scripts\activate` with a "running
scripts is disabled" error, either call `.venv\Scripts\python.exe` directly instead, or run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once (recommended — you'll hit the same
block with npm/npx otherwise).

## Notes / decisions

- Postgres was installed natively (not via Docker) to avoid WSL2/Hyper-V setup on this machine.
  Can be containerized later if useful.
- The full raw Garmin payload is stored per activity (`raw` JSONB column) alongside the
  extracted columns, so later phases (training load, laps, etc.) can backfill new fields
  without needing a re-sync.
- The `Activity` table has a `source` column (currently always `"garmin"`) so another data
  source (e.g. Strava, if you ever get API access) could be added later without a schema change.
- Single-athlete convenience: most endpoints work without `athlete_id` as long as only one
  Garmin account is connected. This will need to change before "other athletes" support (Phase 7).
- Garmin occasionally reports a corrupted `movingDuration` on pool swims (seen: ~193 hours for
  a 61-minute swim). `activities.py` clamps moving time to elapsed time when this happens —
  worth remembering if other odd Garmin fields show up later (elevation gain/loss has also
  shown clearly-wrong values on some activities; not yet worth a fix since nothing depends on
  it yet, but flag it if Phase 4 analytics needs elevation).
- **Windows dev-server quirk:** if you ever run `next dev` from a directory referenced by its
  8.3 short path (e.g. `KYLERC~1` instead of `Kyler Chou`), Next's file watcher crashes with a
  libuv assertion (`fs-event.c` path mismatch). Always launch it via the normal long path.
- **This machine's Application Control policy blocks the `cryptography` package's native (Rust)
  extension** -- confirmed while adding Google Calendar: `import google_auth_oauthlib` fails
  with "An Application Control policy has blocked this file". Any future dependency that pulls
  in `cryptography` (directly or transitively -- lots of auth/crypto-adjacent packages do) will
  hit the same wall. Worth checking for early if a new library's import fails mysteriously.
- **Frontend date-parsing gotcha:** a bare `"YYYY-MM-DD"` string (no time/offset -- e.g.
  resting-HR history dates) parses as UTC midnight per the JS spec. Formatting it with
  `toLocaleDateString()` then renders in the *browser's local* timezone, which silently prints
  the previous day anywhere west of UTC. Full ISO timestamps (with an offset, like activity
  `start_date`) don't have this problem -- only bare dates do. Fix is to anchor to local noon
  first (`` new Date(`${isoDate}T12:00:00`) ``) before formatting; see `formatBareDate` /
  `formatWeekLabel` / `formatShortDate` in `frontend/src/lib/format.ts`, and use the bare-date
  variant for any new bare-date field rather than reaching for the timestamp one (`formatDate`).
- **Backend `created_at` timezone bug (fixed 2026-09-01):** every model's `created_at` used
  `default=datetime.utcnow` -- a *naive* datetime with no timezone tag. psycopg2 stores a naive
  datetime into a `timestamptz` column using the session's local timezone, not literal UTC, so
  every `created_at` in the app (Athlete, Activity, DailyWeather, and initially Task) was
  silently off by the local UTC offset. Caught by comparing a task's `created_at` against its
  `completed_at` (set via the already-correct `datetime.now(timezone.utc)`) and finding a 4-hour
  gap between two timestamps set milliseconds apart. Fixed via a shared `_utcnow()` helper in
  `models.py` -- use that for any new `created_at`-style default, never bare `datetime.utcnow`.
  Existing rows from before the fix keep their wrong stored value (harmless -- nothing reads
  `created_at` for business logic, only display/sort tie-breaking), only new rows are correct.
