# Ironman Coach

A personal training dashboard for Ironman prep: pulls workouts from Garmin (swim/bike/run),
weather, and calendar data; tracks distance/pace/HR/training load/recovery; and will
eventually recommend workouts and explain your data via AI.

## Build plan

1. ✅ **Connect one workout API (Garmin) + database**
2. ✅ **Basic dashboard (Next.js, reads from the API)**
3. ✅ **Weather + calendar data**
4. Training analytics (load, pace/HR trends)
5. Recovery & fitness scores
6. AI-generated recommendations & explanations
7. (later) generalize beyond a single athlete

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
3. **APIs & Services → OAuth consent screen**:
   - User type: **External**
   - Fill in app name, your email as support/developer contact
   - **Test users**: add your own Google account email here — required, or Google will block
     login with "app hasn't completed verification" since this app stays unpublished
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
   - Copy the **Client ID** and **Client Secret** into `backend/.env`

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

### 6. Run the frontend (in a second terminal, backend still running)

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
