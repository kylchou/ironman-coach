import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Athlete
from app.services import strava_client

router = APIRouter(prefix="/auth/strava", tags=["strava-auth"])

# In-memory CSRF state store, fine for a single-user local app. If this ever
# runs multi-instance/production, move this to the DB or a cache.
_pending_states: set[str] = set()


@router.get("/login")
def login():
    """Redirect the browser to Strava's OAuth consent screen."""
    if not settings.strava_client_id or not settings.strava_client_secret:
        raise HTTPException(
            status_code=500,
            detail="STRAVA_CLIENT_ID/STRAVA_CLIENT_SECRET are not set in backend/.env. "
            "Register an app at https://www.strava.com/settings/api first.",
        )
    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    return RedirectResponse(strava_client.authorize_url(state))


@router.get("/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    """Strava redirects here after the user approves (or denies) access."""
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Unknown or expired OAuth state")
    _pending_states.discard(state)

    token_data = strava_client.exchange_code_for_token(code)
    strava_athlete = token_data["athlete"]

    athlete = db.query(Athlete).filter_by(strava_athlete_id=strava_athlete["id"]).one_or_none()
    if athlete is None:
        athlete = Athlete(strava_athlete_id=strava_athlete["id"])
        db.add(athlete)

    athlete.first_name = strava_athlete.get("firstname")
    athlete.last_name = strava_athlete.get("lastname")
    athlete.access_token = token_data["access_token"]
    athlete.refresh_token = token_data["refresh_token"]
    athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)

    db.commit()
    db.refresh(athlete)

    return {
        "message": "Strava account connected.",
        "athlete_id": athlete.id,
        "strava_athlete_id": athlete.strava_athlete_id,
        "name": f"{athlete.first_name} {athlete.last_name}".strip(),
    }
