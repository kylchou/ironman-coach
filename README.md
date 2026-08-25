# Ironman Coach

A personal training dashboard for Ironman prep: pulls workouts from Strava (swim/bike/run),
weather, and calendar data; tracks distance/pace/HR/training load/recovery; and will
eventually recommend workouts and explain your data via AI.

## Build plan

1. ✅ **Connect one workout API (Strava) + database** — this phase
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
│   │   │   ├── strava_auth.py   OAuth login/callback
│   │   │   └── activities.py    Sync from Strava + list from DB
│   │   └── services/
│   │       └── strava_client.py  Strava API wrapper
│   ├── alembic/                Migrations
│   ├── requirements.txt
│   └── .env                    Local secrets (gitignored) — copy from .env.example
└── frontend/                   Phase 2
```

## One-time setup already done on this machine

- Python 3.12, Node.js LTS, PostgreSQL 16 installed via winget
- Database `ironman_coach` created, with a dedicated app role `ironman_app`
  (password lives in `backend/.env`, not committed)
- Python virtualenv created at `backend/.venv`, dependencies installed
- Initial Alembic migration created & applied (`athletes`, `activities` tables)

## What you still need to do

### 1. Register a Strava API app
Go to https://www.strava.com/settings/api and create an app. For "Authorization Callback Domain"
use `localhost`. You'll get a **Client ID** and **Client Secret** — put them in `backend/.env`:

```
STRAVA_CLIENT_ID=your_id
STRAVA_CLIENT_SECRET=your_secret
```

### 2. Run the backend

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 3. Connect your Strava account
Open http://localhost:8000/auth/strava/login in a browser, approve access, and you'll be
redirected back with a confirmation JSON showing your athlete id.

### 4. Pull your activities

```bash
curl -X POST "http://localhost:8000/activities/sync?pages=3"
curl "http://localhost:8000/activities?sport_type=Run"
```

Interactive API docs are always at http://localhost:8000/docs once the server is running.

## Notes / decisions

- Postgres was installed natively (not via Docker) to avoid WSL2/Hyper-V setup on this machine.
  Can be containerized later if useful.
- The full raw Strava payload is stored per activity (`raw` JSONB column) alongside the
  extracted columns, so later phases (training load, laps, etc.) can backfill new fields
  without needing a Strava re-sync.
- Single-athlete convenience: most endpoints work without `athlete_id` as long as only one
  Strava account is connected. This will need to change before "other athletes" support (Phase 7).
