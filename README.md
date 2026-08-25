# Ironman Coach

A personal training dashboard for Ironman prep: pulls workouts from Garmin (swim/bike/run),
weather, and calendar data; tracks distance/pace/HR/training load/recovery; and will
eventually recommend workouts and explain your data via AI.

## Build plan

1. ✅ **Connect one workout API (Garmin) + database** — this phase
2. Basic dashboard (Next.js, reads from the API)
3. Weather + calendar data
4. Training analytics (load, pace/HR trends)
5. Recovery & fitness scores
6. AI-generated recommendations & explanations
7. (later) generalize beyond a single athlete

## Stack

- **Backend:** Python 3.12 / FastAPI, SQLAlchemy 2.0, Alembic migrations
- **Database:** PostgreSQL 16 (installed locally as a native Windows service)
- **Frontend:** React / Next.js — not scaffolded yet, comes in Phase 2

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
└── frontend/                   Phase 2
```

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
curl -X POST "http://localhost:8000/activities/sync?pages=3"
curl "http://localhost:8000/activities?sport_type=Run"
```

Interactive API docs are always at http://localhost:8000/docs once the server is running.

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
